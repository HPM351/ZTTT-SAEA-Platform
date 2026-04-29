import subprocess
import sys
import os
import time
import atexit

# 存放进程对象的列表，用于随手清理
processes = []

def cleanup():
    """退出时自动干掉所有子进程，绝不留幽灵进程"""
    print("\n🛑 收到停止信号，正在安全关闭前后端服务...")
    for p in processes:
        try:
            p.terminate()
        except:
            pass
    print("👋 所有服务已安全退出！")

# 注册退出清理函数
atexit.register(cleanup)

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "hpm-frontend")

    print("=" * 50)
    print("🚀 正在为您启动 HPM_OPT_WEB 全栈环境...")
    print("=" * 50)

    try:
        # 1. 启动后端 (静默使用当前的虚拟环境)
        print(">>> 启动 FastAPI 后端...")
        backend_process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=root_dir,
            shell=False
        )
        processes.append(backend_process)

        # 稍微等 2 秒，让后端的端口先占好
        time.sleep(2)

        # 2. 启动前端 (使用 npm 命令)
        print(">>> 启动 Vue Vite 前端...")
        # Windows 下执行 npm 需要 shell=True
        frontend_process = subprocess.Popen(
            "npm run dev",
            cwd=frontend_dir,
            shell=True
        )
        processes.append(frontend_process)

        print("\n🎉 全栈服务已就绪！日志将统一打印在下方 (按 Ctrl+C 或点击 IDE 停止按钮可一键关闭)\n")
        print("-" * 50)

        # 保持主进程不死，监听子进程的日志
        backend_process.wait()
        frontend_process.wait()

    except KeyboardInterrupt:
        # 捕获用户手动终止
        sys.exit(0)

if __name__ == "__main__":
    main()