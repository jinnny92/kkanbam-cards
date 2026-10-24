"""깐밤AI 표지 카드 -> 릴스용 세로 영상.

usage:
  python3 make_reel.py <cover.png> <out.mp4>
    -> 1080x1350 표지를 1080x1920 캔버스 가운데에 두고 위아래를 카드 배경색으로 채운
       3초 / 30fps / H.264(high, yuv420p) / +faststart / 무음 AAC(44.1kHz) mp4를 만든다.
"""
import json, pathlib, subprocess, sys

BG = "0x0D1530"  # render_cards.py 의 BG(#0D1530)와 동일
W, H, SEC, FPS = 1080, 1920, 3, 30

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
if not src.is_file():
    raise SystemExit(f"cover not found: {src}")
out.parent.mkdir(parents=True, exist_ok=True)

vf = (f"scale={W}:-2:force_original_aspect_ratio=decrease,"
      f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={BG},format=yuv420p")
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-loop", "1", "-framerate", str(FPS), "-i", str(src),
    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
    "-vf", vf, "-t", str(SEC), "-r", str(FPS),
    "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
    "-shortest", "-movflags", "+faststart", str(out),
], check=True)

info = json.loads(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate",
     "-of", "json", str(out)], capture_output=True, text=True, check=True).stdout)
fmt = info["format"]
streams = ", ".join(
    f'{s["codec_type"]}:{s["codec_name"]}' + (f' {s["width"]}x{s["height"]}@{s["r_frame_rate"]}' if s["codec_type"] == "video" else "")
    for s in info["streams"])
print(f"REEL {out} size={int(fmt['size'])/1024:.1f}KB duration={float(fmt['duration']):.2f}s [{streams}]")
