"""
GIF → 128×64 单色 OLED 帧数组转换工具
输出到项目 src/ 目录
"""

import os
from PIL import Image

GIF_PATH = r"C:\Users\Alan Qi\Desktop\1e78d601061d43d991db7adedbeba0b1.gif"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")

def gif_to_oled_array(gif_path, out_dir):
    img = Image.open(gif_path)
    frames = []
    delays = []
    gray_frames = []  # 保存预处理后的灰度帧，用于统一算阈值

    print(f"共 {img.n_frames} 帧，正在预处理...")

    TARGET_W, TARGET_H = 128, 64

    from PIL import ImageFilter, ImageOps
    import numpy as np

    # ============ 第一遍：预处理所有帧，收集灰度图 ============
    for i in range(img.n_frames):
        img.seek(i)
        gray = img.convert("L")

        # 保持宽高比缩放到 128x64（加白边居中）
        gray.thumbnail((TARGET_W, TARGET_H), Image.LANCZOS)
        canvas = Image.new("L", (TARGET_W, TARGET_H), 255)
        x = (TARGET_W - gray.width) // 2
        y = (TARGET_H - gray.height) // 2
        canvas.paste(gray, (x, y))
        gray = canvas

        # 轻度锐化（先不做对比度拉伸，等全局统一处理）
        gray = gray.filter(ImageFilter.SHARPEN)

        gray_frames.append(gray)
        delays.append(img.info.get("duration", 100))

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{img.n_frames}")

    # ============ 背景色分析 ============
    print("分析背景色...")

    # 用第一帧边缘像素估算背景亮度
    first = np.array(gray_frames[0])
    h, w = first.shape
    edge_pixels = np.concatenate([
        first[0, :], first[h-1, :],
        first[:, 0], first[:, w-1],
    ])
    bg_value = int(np.median(edge_pixels))
    print(f"边缘背景色中位数: {bg_value}")

    # 统一阈值：背景纯黑，内容纯白
    if bg_value > 200:
        # 背景很亮 → 内容在低亮度区（< bg_value-40 算内容）
        content_max = bg_value - 40
        unified_threshold = content_max
        print(f"背景偏亮({bg_value})，阈值={unified_threshold}，背景→黑色")
    else:
        # 背景偏暗 → 内容在高亮度区
        content_min = bg_value + 40
        unified_threshold = content_min
        print(f"背景偏暗({bg_value})，阈值={unified_threshold}，背景→黑色")

    # ============ 第二遍：统一阈值二值化 ============
    print("正式转换...")
    for i, gray in enumerate(gray_frames):
        if bg_value > 200:
            # 背景偏亮 → 亮度≥阈值的内容变白，背景(高亮度)变黑
            bw = gray.point(lambda x: 0 if x >= unified_threshold else 255, "1")
        else:
            # 背景偏暗 → 亮度<阈值的内容变白，背景(低亮度)变黑
            bw = gray.point(lambda x: 0 if x < unified_threshold else 255, "1")

        pixels = []
        for y in range(64):
            for x in range(0, 128, 8):
                byte = 0
                for b in range(8):
                    if x + b < 128:
                        px = bw.getpixel((x + b, y))
                        if px == 0:
                            byte |= (1 << b)
                pixels.append(byte)

        frames.append(pixels)

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(gray_frames)}")

    print(f"转换完成！共 {len(frames)} 帧")

    total_bytes = len(frames) * 1024
    print(f"总内存: {total_bytes} 字节 ({total_bytes/1024:.1f} KB)")
    if total_bytes > 3 * 1024 * 1024:
        print("⚠️ 警告：超过 3MB，建议减少帧数")

    name = os.path.splitext(os.path.basename(gif_path))[0].replace(" ", "_").replace("-", "_")
    # 确保宏名不以数字开头
    guard_name = name.upper()
    if guard_name[0].isdigit():
        guard_name = "GIF_" + guard_name
    out_path = os.path.join(out_dir, name + ".h")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"// 由 gif2oled.py 自动生成 - {gif_path}\n")
        f.write(f"// 帧数: {len(frames)}, 每帧: 1024 字节\n\n")
        f.write(f"#ifndef {guard_name}_H\n#define {guard_name}_H\n\n")
        f.write(f"#define FRAME_COUNT {len(frames)}\n")
        f.write(f"#define FRAME_DELAYS_MS {{{', '.join(map(str, delays))}}}\n\n")

        for i, frame_data in enumerate(frames):
            f.write(f"// 帧 {i} (延时: {delays[i]}ms)\n")
            f.write(f"static const unsigned char frame{i}[] PROGMEM = {{\n")
            for j in range(0, len(frame_data), 16):
                chunk = frame_data[j:j + 16]
                line = ", ".join(f"0x{b:02x}" for b in chunk)
                f.write(f"  {line},\n")
            f.write("};\n\n")

        f.write("// 所有帧的指针数组\n")
        f.write("static const unsigned char* const frames[] PROGMEM = {\n")
        for i in range(len(frames)):
            f.write(f"  frame{i},\n")
        f.write("};\n\n")
        f.write("#endif\n")

    print(f"已保存到: {out_path}")
    return out_path


if __name__ == "__main__":
    gif_to_oled_array(GIF_PATH, OUTPUT_DIR)
