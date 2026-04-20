@echo off
chcp 65001 >nul
title ZTTT RM 优化控制台 - 启动器

:: 【核心修复】强制切换到当前 bat 脚本所在的绝对目录
cd /d "%~dp0"

echo ==========================================
echo    ZTTT RM Optimizer - 一键启动程序
echo ==========================================
echo.

echo [1/2] 🚀 正在启动 FastAPI 后端引擎 (端口:8001)...
:: 弹出一个新窗口运行 Python 后端
start "FastAPI Backend Engine" cmd /k "python engine.py"

:: 稍微等待 2 秒，确保后端服务先就绪
timeout /t 2 /nobreak >nul

echo [2/2] 💻 正在启动 Vue3 现代化前端...
:: 进入前端文件夹并启动 Vite
cd frontend
start "Vue3 Frontend UI" cmd /k "npm run dev"

echo.
echo ✅ 所有服务均已成功发起启动指令！
echo ------------------------------------------
echo 后端 API 接口 : http://127.0.0.1:8001
echo 前端 UI 界面  : http://localhost:5173
echo ------------------------------------------
echo.
echo ⚠️ 使用说明：
echo 1. 此时系统应该弹出了两个新的黑框，请不要关闭它们。
echo 2. 前端编译完成后，通常会自动在浏览器中打开网页。
echo 3. 如果想结束优化程序，直接点击右上角的 [X] 关闭那两个弹出的黑框即可。
echo.
pause