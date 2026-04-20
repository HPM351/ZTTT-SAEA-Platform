from PIL import Image
import os

# 👇 把这里换成你电脑上真实的 .ico 文件绝对路径
ico_path = r"D:\pycharm\PyCharm 2026.1\bin\pycharm.ico"
output_png = "pycharm-logo.png"

try:
    if not os.path.exists(ico_path):
        print(f"❌ 找不到文件: {ico_path}")
    else:
        # 打开 ico 文件
        img = Image.open(ico_path)

        # 将其保存为背景透明的 PNG 格式
        img.save(output_png, format="PNG")
        print(f"✅ 转换成功！已在当前目录生成: {output_png}")

except Exception as e:
    print(f"⚠️ 转换失败: {e}")