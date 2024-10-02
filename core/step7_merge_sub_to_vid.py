import os
import subprocess
import time
import sys
import platform
import numpy as np
import cv2
from rich import print as rprint

# 将父目录添加到路径（如果需要）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.step1_ytdlp import find_video_files

# 字体相关设置
SRC_FONT_SIZE = 14
TRANS_FONT_SIZE = 16
# 使用 SmileySans-Oblique.otf 字体
FONT_NAME = 'Smiley Sans Oblique'  # 字体名称，根据 fc-list 的输出
TRANS_FONT_NAME = 'Smiley Sans Oblique'
# 字体文件路径
FONT_FILE = '/usr/share/fonts/truetype/SmileySans-Oblique.otf'

# 字幕样式设置
SRC_FONT_COLOR = '&HFFFFFF'        # 白色
SRC_OUTLINE_COLOR = '&H000000'     # 黑色
SRC_OUTLINE_WIDTH = 1
SRC_SHADOW_COLOR = '&H80000000'    # 半透明黑色

TRANS_FONT_COLOR = '&HFFFFFF'      # 白色
TRANS_OUTLINE_COLOR = '&H000000'   # 黑色
TRANS_OUTLINE_WIDTH = 1
# 移除背景颜色
# TRANS_BACK_COLOR = '&H33000000'  # 注释掉，不需要背景色

def merge_subtitles_to_video():
    from config import RESOLUTION
    TARGET_WIDTH, TARGET_HEIGHT = RESOLUTION.split('x')
    video_file = find_video_files()
    output_video = "output/output_video_with_subs.mp4"
    os.makedirs(os.path.dirname(output_video), exist_ok=True)

    # 检查分辨率
    if RESOLUTION == '0x0':
        rprint("[bold yellow]Warning: A 0-second black video will be generated as a placeholder as Resolution is set to 0x0.[/bold yellow]")

        # 创建黑色帧
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, 1, (1920, 1080))
        out.write(frame)
        out.release()

        rprint("[bold green]Placeholder video has been generated.[/bold green]")
        return

    en_srt = "output/src_subtitles.srt"
    trans_srt = "output/trans_subtitles.srt"

    if not os.path.exists(en_srt) or not os.path.exists(trans_srt):
        print("Subtitle files not found in the 'output' directory.")
        exit(1)

    # 确定是否是macOS
    macOS = os.name == 'posix' and platform.system() == 'Darwin'

    # 构建FFmpeg命令
    ffmpeg_cmd = [
        'ffmpeg', '-i', video_file,
        '-vf', (
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            # 对于第一个字幕文件（源字幕）
            f"subtitles='{en_srt}':force_style='"
            f"FontSize={SRC_FONT_SIZE},"
            f"fontfile={FONT_FILE},"
            f"PrimaryColour={SRC_FONT_COLOR},"
            f"OutlineColour={SRC_OUTLINE_COLOR},"
            f"OutlineWidth={SRC_OUTLINE_WIDTH},"
            f"ShadowColour={SRC_SHADOW_COLOR},"
            f"BorderStyle=1'"
            ','
            # 对于第二个字幕文件（翻译字幕）
            f"subtitles='{trans_srt}':force_style='"
            f"FontSize={TRANS_FONT_SIZE},"
            f"fontfile={FONT_FILE},"
            f"PrimaryColour={TRANS_FONT_COLOR},"
            f"OutlineColour={TRANS_OUTLINE_COLOR},"
            f"OutlineWidth={TRANS_OUTLINE_WIDTH},"
            f"BorderStyle=1,"        # 设置边框样式为1
            f"Shadow=0,"             # 如果不需要阴影，设置为0
            f"Alignment=2,"
            f"MarginV=25'"
        ),
        '-y',
        output_video
    ]

    # 根据是否是macOS添加不同的参数, macOS的ffmpeg不包含preset
    if not macOS:
        ffmpeg_cmd.insert(-2, '-preset')
        ffmpeg_cmd.insert(-2, 'veryfast')

    print("🎬 Start merging subtitles to video...")
    start_time = time.time()
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')

    try:
        for line in process.stdout:
            print(line, end='')  # 实时打印FFmpeg输出

        process.wait()
        if process.returncode == 0:
            print(f"\n[Process completed in {time.time() - start_time:.2f} seconds.]")
            print("🎉🎥 Subtitles merging to video completed! Please check in the `output` folder 👀")
        else:
            print("\n[Error occurred during FFmpeg execution.]")
    except KeyboardInterrupt:
        process.kill()
        print("\n[Process interrupted by user.]")
    except Exception as e:
        print(f"\n[An unexpected error occurred: {e}]")
        if process.poll() is None:
            process.kill()

if __name__ == "__main__":
    merge_subtitles_to_video()
