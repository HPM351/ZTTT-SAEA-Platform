import os


def run_setup():
    print("\n" + "=" * 60)
    print("欢迎使用 HPM_OPT_WEB (高功率微波优化 Web 平台)")
    print("=" * 60)
    print("检测到您是首次运行项目，或者尚未配置环境变量。")
    print("我们将通过几个简单的问题帮您完成初始化...\n")

    # 1. 引导 CST 路径配置 (默认指向你本地能跑通的 D 盘路径)
    default_cst = r"D:\CST Studio Suite 2024\AMD64\python_cst_libraries"
    print("[1/2] 配置 CST Python 运行库路径")
    print(f"推荐的默认路径为: {default_cst}")

    while True:
        cst_path = input("👉 请输入您的 CST 路径 (直接回车则使用默认路径):\n> ").strip()

        # 处理直接回车的情况
        if not cst_path:
            cst_path = default_cst

        # 去除用户可能不小心粘贴带进来的双引号
        cst_path = cst_path.strip('"\'')

        # 简单验证路径是否存在
        if os.path.exists(cst_path):
            print("验证通过：CST 路径有效！\n")
            break
        else:
            print("警告：未在您的电脑上找到该目录！")
            retry = input("是否确认要强制使用该未知路径？(y/n) [默认: n]: ").strip().lower()
            if retry == 'y':
                break
            print("-" * 40)

    # 2. 引导 LLM API 配置 (非强制)
    print("[2/2] 配置大语言模型 API Key (用于智能分析模块)")
    llm_key = input("请输入您的 API Key (可选，直接回车可跳过):\n> ").strip()

    # 3. 写入 .env 文件
    env_content = f"""# ==========================================
# 平台运行环境变量配置 (由 setup_env.py 自动生成)
# ==========================================

# CST 引擎配置
CST_PYTHON_PATH="{cst_path}"

# 数据库配置 (默认使用当前目录下的 saea_data.db)
DB_PATH="sqlite:///./saea_data.db"

# LLM 接口配置
LLM_API_KEY="{llm_key}"
LLM_BASE_URL="https://api.openai.com/v1"

# Web 服务配置
HOST="0.0.0.0"
PORT=8000
"""
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    print("\n配置完成！已成功为您生成 .env 环境变量文件。")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_setup()