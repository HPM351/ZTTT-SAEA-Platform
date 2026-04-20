# engine/llm_service.py
import os
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

llm_router = APIRouter(prefix="/api/llm", tags=["LLM Assistant"])


class ChatRequest(BaseModel):
    message: str
    history: list = []
    agent_id: str = "main"
    images_base64_list: list[str] = []


@llm_router.post("/chat")
async def chat_with_dual_track(req: ChatRequest):
    # ==========================================
    # 1. 配置参数区
    # ==========================================
    # 硅基流动官方直连配置 (视觉路线)
    SILICONFLOW_URL = "https://api.siliconflow.cn/v1/chat/completions"
    SILICONFLOW_KEY = "sk-ypnnksenlishqzdhkrcoiqrgmrjsjqibkawsbpxcnkywxbhp"
    VISION_MODEL = "Qwen/Qwen3.5-397B-A17B"

    # OpenClaw 本地网关配置 (文本控制路线)
    OPENCLAW_URL = "http://127.0.0.1:18789/v1/chat/completions"
    OPENCLAW_TOKEN = "123456"

    # ==========================================
    # 2. 路由分流判定
    # ==========================================
    # 只要有图片，或者 agent 是 vision，就走直连
    use_vision_bypass = (req.agent_id == "vision") or (len(req.images_base64_list) > 0)

    # 加载系统提示词
    prompt_filename = "saea_vision.md" if req.agent_id == "vision" else "saea_main.md"
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", prompt_filename)
    saea_soul = "你是一个 SAEA 平台助手。"
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            saea_soul = f.read()

    if use_vision_bypass:
        # 🚀 路线 A：视觉直通车
        target_url = SILICONFLOW_URL
        target_token = SILICONFLOW_KEY
        target_model = VISION_MODEL

        # 组装符合 OpenAI Vision 标准的多模态 Content (图片在前，文字在后)
        user_content = []
        for img_b64 in req.images_base64_list:
            user_content.append({"type": "image_url", "image_url": {"url": img_b64}})
        user_content.append({"type": "text", "text": req.message or "请分析提供的图像。"})

        # 对于视觉模型，历史记录也需要做简单的清洗或格式化
        formatted_history = []
        for m in req.history:
            formatted_history.append({"role": m['role'], "content": m['content']})
    else:
        # 🐢 路线 B：OpenClaw 文本指令网关
        target_url = OPENCLAW_URL
        target_token = OPENCLAW_TOKEN
        target_model = f"openclaw:{req.agent_id}"
        user_content = req.message
        formatted_history = req.history

    # ==========================================
    # 3. 统一请求封装
    # ==========================================
    messages = [{"role": "system", "content": saea_soul}] + formatted_history + [
        {"role": "user", "content": user_content}]

    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": 0.7,
        "stream": True
    }

    headers = {
        "Authorization": f"Bearer {target_token}",
        "Content-Type": "application/json"
    }

    async def stream_generator():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", target_url, json=payload, headers=headers, timeout=180.0) as response:
                    if response.status_code != 200:
                        error_detail = await response.aread()
                        yield f"data: {{\"error\": \"API响应错误: {error_detail.decode()}\"}}\n\n".encode("utf-8")
                        return

                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as e:
            yield f"data: {{\"error\": \"后端路由异常: {str(e)}\"}}\n\n".encode("utf-8")

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 专门用来破除 Nginx/反代 缓冲的终极指令
        }
    )