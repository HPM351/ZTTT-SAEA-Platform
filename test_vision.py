import base64
import requests
import json
import os

# ==========================================
# 1. 配置参数 (请确保和你的 OpenClaw 后端一致)
# ==========================================
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_TOKEN = "sk-ypnnksenlishqzdhkrcoiqrgmrjsjqibkawsbpxcnkywxbhp"
MODEL_NAME = "Qwen/Qwen3.5-397B-A17B" # 这是你配置里的原话
IMAGE_PATH = "test.png"  # 替换为你本地测试图片的真实路径


# ==========================================
# 2. 图片转 Base64 助手函数
# ==========================================
def encode_image_to_base64(image_path):
    if not os.path.exists(image_path):
        print(f"❌ 找不到图片文件: {image_path}")
        return None
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def main():
    base64_image = encode_image_to_base64(IMAGE_PATH)
    if not base64_image:
        return

    # ==========================================
    # 3. 组装最纯正的 OpenAI 多模态 JSON Payload
    # ==========================================
    # 注意：大多数标准框架需要带上前缀，如果报错可以尝试把前缀去掉
    image_url = f"data:image/jpeg;base64,{base64_image}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": "仔细分析这张图片，告诉我你看到了什么波形？"
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "stream": False  # 测试脚本先不开流式，直接看最终结果方便排查
    }

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"🚀 正在向 {API_URL} 发送纯净的多模态请求...")

    # ==========================================
    # 4. 发送请求并捕获详尽的报错信息
    # ==========================================
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            print("\n✅ 请求成功！模型回复如下：")
            result = response.json()
            print("-" * 50)
            print(result['choices'][0]['message']['content'])
            print("-" * 50)
        else:
            print(f"\n❌ 请求失败，HTTP 状态码: {response.status_code}")
            print("后端详细报错信息:")
            print(response.text)

    except Exception as e:
        print(f"\n💥 发生代码级异常: {str(e)}")


if __name__ == "__main__":
    main()