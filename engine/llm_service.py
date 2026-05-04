# engine/llm_service.py
import os
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi import Depends
from engine.api_chat_history import get_current_user
llm_router = APIRouter(prefix="/api/llm", tags=["LLM Assistant"])
import base64
import io
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

class ChatRequest(BaseModel):
    message: str
    history: list = []
    agent_id: str = "main"
    images_base64_list: list[str] = []


class VisionChatRequest(BaseModel):
    message: str
    history: list = []
    images_base64_list: list[str] = []

# 专门为文献助手（文本模型）定义的请求体，增加 session_id 确保严密隔离
class TextChatRequest(BaseModel):
    message: str
    history: list = []
    session_id: str = "default_session"
    files: list = []

# ==========================================
# 1. 文献助手专属路由 (纯文本)
# ==========================================
# ==========================================
# 1. 文献助手专属路由 (纯文本)
# ==========================================
@llm_router.post("/chat/text")
async def chat_with_text_model(req: TextChatRequest, current_user = Depends(get_current_user)):
    # 1. 打印日志：不仅能消除 current_user 的灰色警告，还能在后端控制台清晰看到是谁在请求
    print(f"🚀 收到来自研究员 [{current_user.username}] 的文献对话请求 (Session: {req.session_id})")

    OPENCLAW_URL = "http://127.0.0.1:18789/v1/chat/completions"
    OPENCLAW_TOKEN = "123456"
    target_model = "openclaw:main"

    # 2. 加载知识库 Prompt (灵魂文档)
    base_soul = "你是一个专业的高功率微波与计算机科学文献助手。请基于专业知识准确回答。"
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", "saea_main.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            base_soul = f.read()

    # 3. 动态注入：把当前用户的身份追加到灵魂文档的最末尾
    dynamic_soul = f"{base_soul}\n\n[系统附加信息]：当前与你对话的研究员是：{current_user.username}。"

    # 4. 组装消息流
    extracted_text = ""
    if hasattr(req, 'files') and req.files:
        for file in req.files:
            file_name = file.get("name", "")
            file_type = file.get("type", "")
            base64_content = file.get("content", "")

            if "," in base64_content:
                base64_content = base64_content.split(",", 1)[1]

            try:
                file_bytes = base64.b64decode(base64_content)

                # --- 原有的 TXT 解析 ---
                if "text/plain" in file_type or file_name.lower().endswith(".txt"):
                    extracted_text += f"\n\n--- 附件 [{file_name}] 内容开始 ---\n"
                    extracted_text += file_bytes.decode("utf-8", errors="ignore")
                    extracted_text += f"\n--- 附件 [{file_name}] 内容结束 ---\n"

                # --- 原有的 PDF 解析 ---
                elif "application/pdf" in file_type or file_name.lower().endswith(".pdf"):
                    extracted_text += f"\n\n--- 附件 [{file_name}] 内容开始 ---\n"
                    if PyPDF2:
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                        for page in pdf_reader.pages:
                            text = page.extract_text()
                            if text:
                                extracted_text += text + "\n"
                    else:
                        extracted_text += "[提示：后端未安装 PyPDF2]\n"
                    extracted_text += f"\n--- 附件 [{file_name}] 内容结束 ---\n"

                # --- 【新增】Word (.docx) 解析 ---
                elif "wordprocessingml.document" in file_type or file_name.lower().endswith(".docx"):
                    extracted_text += f"\n\n--- 附件 [{file_name}] 内容开始 ---\n"
                    if docx:
                        doc = docx.Document(io.BytesIO(file_bytes))
                        # 提取所有段落文字
                        for para in doc.paragraphs:
                            if para.text.strip():
                                extracted_text += para.text + "\n"
                        # 如果需要，也可以提取表格文字
                        for table in doc.tables:
                            for row in table.rows:
                                row_data = [cell.text.strip() for cell in row.cells]
                                extracted_text += " | ".join(row_data) + "\n"
                    else:
                        extracted_text += "[提示：后端未安装 python-docx 库]\n"
                    extracted_text += f"\n--- 附件 [{file_name}] 内容结束 ---\n"

                else:
                    extracted_text += f"\n\n--- 附件 [{file_name}] --- (暂不支持此格式)\n"
            except Exception as e:
                print(f"解析 {file_name} 失败: {e}")

    # 5. 组装最终的用户提问（将解析出来的文件文本作为上下文注入）
    final_user_message = req.message
    if extracted_text:
        final_user_message += f"\n\n以下是用户提供的参考资料，请结合上述问题和资料进行回答：{extracted_text}"

    # 6. 组装消息流
    messages = [{"role": "system", "content": dynamic_soul}] + req.history + [
        {"role": "user", "content": final_user_message}]

    # 注意：通过 user 字段传递 session_id 可以让底层 OpenAI 格式网关避免多用户并发串行
    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": 0.7,
        "stream": True,
        "user": req.session_id
    }

    headers = {
        "Authorization": f"Bearer {OPENCLAW_TOKEN}",
        "Content-Type": "application/json"
    }

    async def stream_generator():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", OPENCLAW_URL, json=payload, headers=headers, timeout=180.0) as response:
                    if response.status_code != 200:
                        error_detail = await response.aread()
                        yield f"data: {{\"error\": \"API响应错误: {error_detail.decode()}\"}}\n\n".encode("utf-8")
                        return
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as e:
            yield f"data: {{\"error\": \"后端文本路由异常: {str(e)}\"}}\n\n".encode("utf-8")

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# ==========================================
# 2. 视觉核心专属路由 (多模态)
# ==========================================
@llm_router.post("/chat/vision")
async def chat_with_vision_model(req: VisionChatRequest):
    SILICONFLOW_URL = "https://api.siliconflow.cn/v1/chat/completions"
    SILICONFLOW_KEY = "sk-ypnnksenlishqzdhkrcoiqrgmrjsjqibkawsbpxcnkywxbhp"
    VISION_MODEL = "Qwen/Qwen3.5-397B-A17B"

    saea_soul = "你是一个 SAEA 平台视觉助手，专门用于分析图表和物理曲线。"
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", "saea_vision.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            saea_soul = f.read()

    user_content = []
    for img_b64 in req.images_base64_list:
        user_content.append({"type": "image_url", "image_url": {"url": img_b64}})
    user_content.append({"type": "text", "text": req.message or "请分析提供的图像。"})

    messages = [{"role": "system", "content": saea_soul}] + req.history + [{"role": "user", "content": user_content}]

    payload = {
        "model": VISION_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "stream": True
    }

    headers = {
        "Authorization": f"Bearer {SILICONFLOW_KEY}",
        "Content-Type": "application/json"
    }

    async def stream_generator():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", SILICONFLOW_URL, json=payload, headers=headers, timeout=180.0) as response:
                    if response.status_code != 200:
                        error_detail = await response.aread()
                        yield f"data: {{\"error\": \"API响应错误: {error_detail.decode()}\"}}\n\n".encode("utf-8")
                        return
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as e:
            yield f"data: {{\"error\": \"后端视觉路由异常: {str(e)}\"}}\n\n".encode("utf-8")

    return StreamingResponse(stream_generator(), media_type="text/event-stream")