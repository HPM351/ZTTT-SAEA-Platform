import os
from icoextract import IconExtractor
from PIL import Image


def extract_and_convert(exe_path, output_png_name):
    if not os.path.exists(exe_path):
        print(f"❌ 找不到文件: {exe_path}")
        return

    ico_path = "temp.ico"
    try:
        # 1. 从 exe 中提取 .ico 图标
        extractor = IconExtractor(exe_path)
        extractor.export_icon(ico_path)

        # 2. 使用 Pillow 将 .ico 转为 Web 支持的 .png
        img = Image.open(ico_path)

        # .ico 文件通常包含多个尺寸，我们强制选择最大尺寸 (通常是 256x256)
        img.save(output_png_name, format="PNG")
        print(f"✅ 成功提取并生成: {output_png_name}")

    except Exception as e:
        print(f"⚠️ 提取 {output_png_name} 失败: {e}")
    finally:
        # 清理临时的 .ico 文件
        if os.path.exists(ico_path):
            os.remove(ico_path)


if __name__ == "__main__":
    # 👇 请将下面这两个路径替换为你电脑上真实的软件绝对路径！

    # 提取 CST 图标 (路径请根据你的实际安装位置修改)
    cst_exe_path = r"D:\CST Studio Suite 2024\CST DESIGN ENVIRONMENT.exe"
    extract_and_convert(cst_exe_path, "cst-logo.png")

    # 提取 PyCharm 图标 (路径请根据你的实际安装位置修改)
    pycharm_exe_path = r"D:\pycharm\PyCharm 2026.1\bin\pycharm64.exe"
    extract_and_convert(pycharm_exe_path, "pycharm-logo.png")