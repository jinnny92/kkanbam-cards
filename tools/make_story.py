"""깐밤AI 홍보 스토리 (1080x1920 PNG): 밤·나무 도마 배경 위에 그날 날짜와 제목을 얹는다.

usage:
  python3 tools/make_story.py <출력 PNG> <data.json> [배경 이미지, 기본 assets/story_bg.png]

data.json 예:
  {"date_label": "10월 24일 토요일", "items": ["제목1", "제목2", "제목3", "제목4", "제목5"]}
  items는 3~5개, 한 줄 20자 안팎. 길면 그 줄만 글자가 자동으로 작아진다.

배경은 폭 1080으로 맞춘 뒤 높이 1920으로 가운데를 잘라 쓴다. 아래 좌표는 그 기준.
도마 위 글씨는 도마 기울기(반시계 약 2도)만큼 돌려서 얹는다.
폰트: Noto Sans KR 가변 폰트 → 없으면 Noto Sans CJK(KR) → KKANBAM_FONT 환경변수로 지정 가능.
"""
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
BROWN, GOLD, CREAM = (62, 40, 24), (236, 194, 116), (234, 222, 200)
BOARD_TILT = 2.0
BOARD_CENTER = (545, 940)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_VF = [os.environ.get("KKANBAM_FONT", ""), "C:/Windows/Fonts/NotoSansKR-VF.ttf"] + \
      glob.glob("/usr/share/fonts/**/NotoSansKR*.ttf", recursive=True)
_CJK = {w: glob.glob(f"/usr/share/fonts/**/NotoSansCJK-{w}.ttc", recursive=True) for w in ("Regular", "Medium", "Bold")}
_cache = {}

def font(size, weight):
    key = (size, weight)
    if key in _cache:
        return _cache[key]
    for path in _VF:
        if path and os.path.exists(path):
            f = ImageFont.truetype(path, size)
            try:
                f.set_variation_by_axes([weight])
            except OSError:
                pass
            _cache[key] = f
            return f
    name = "Regular" if weight < 450 else "Medium" if weight < 600 else "Bold"
    files = _CJK[name] or _CJK["Regular"] or _CJK["Bold"]
    if not files:
        sys.exit("한글 폰트를 찾지 못했어요. KKANBAM_FONT로 지정하거나 fonts-noto-cjk를 설치하세요.")
    for idx in range(10):  # TTC 안에서 KR 폰트를 찾는다
        try:
            f = ImageFont.truetype(files[0], size, index=idx)
        except OSError:
            break
        if "KR" in f.getname()[0]:
            _cache[key] = f
            return f
    _cache[key] = ImageFont.truetype(files[0], size)
    return _cache[key]

def _draw(d, xy, s, fnt, fill, anchor, spacing):
    if not spacing:
        d.text(xy, s, font=fnt, fill=fill, anchor=anchor)
        return
    total = sum(d.textlength(c, font=fnt) for c in s) + spacing * (len(s) - 1)
    x = xy[0] - (total / 2 if anchor[0] == "m" else 0)
    for c in s:
        d.text((x, xy[1]), c, font=fnt, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(c, font=fnt) + spacing

def text(layer, xy, s, fnt, fill, shadow=(0, 0, 0, 110), off=2, blur=3, anchor="la", spacing=0):
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    _draw(ImageDraw.Draw(sh), (xy[0] + off, xy[1] + off), s, fnt, shadow, anchor, spacing)
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    _draw(ImageDraw.Draw(layer), xy, s, fnt, fill, anchor, spacing)

def main(out_path, data_path, bg_path=os.path.join(ROOT, "assets", "story_bg.png")):
    d = json.load(open(data_path, encoding="utf-8"))
    bg = Image.open(bg_path).convert("RGBA")
    bg = bg.resize((W, round(bg.height * W / bg.width)), Image.LANCZOS)
    top = max(0, (bg.height - H) // 2)
    img = bg.crop((0, top, W, top + H))

    glow = (255, 244, 220, 140)
    text(img, (W // 2, 205), f"NEW · {d['date_label']}", font(36, 600), BROWN, glow, 0, 6, "mm", 2)
    text(img, (W // 2, 298), "오늘의 AI 소식", font(84, 700), BROWN, glow, 0, 8, "mm", -1)
    text(img, (W // 2 - 36, 400), "올라왔어요", font(84, 700), BROWN, glow, 0, 8, "mm", -1)

    # 도마 위: 칼(x≈715~)과 국자(y≈1300~)를 피해 x 215~690 안에 쓰고 도마 기울기만큼 돌린다
    board = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = 215
    text(board, (x, 608), "깐밤AI", font(30, 700), GOLD, spacing=1)
    text(board, (x, 652), f"{d['date_label']} 아침", font(28, 400), GOLD, spacing=1)
    text(board, (x, 712), "간밤의", font(76, 700), GOLD, off=3, blur=5, spacing=-1)
    text(board, (x, 800), "AI 소식", font(76, 700), GOLD, off=3, blur=5, spacing=-1)
    text(board, (x, 920), "자는 동안 일어난 AI 이야기, 5분 요약", font(26, 400), CREAM)
    y, max_w = 990, 690 - (x + 40)
    draw = ImageDraw.Draw(board)
    for i, t in enumerate(d["items"][:5], 1):
        size = 30
        while size > 22 and draw.textlength(t, font=font(size, 500)) > max_w:
            size -= 1
        text(board, (x, y), f"{i}", font(30, 700), GOLD)
        text(board, (x + 40, y + (30 - size) // 2), t, font(size, 500), CREAM)
        y += 56
    img.alpha_composite(board.rotate(BOARD_TILT, resample=Image.BICUBIC, center=BOARD_CENTER))

    text(img, (W // 2, 1590), "피드에서 카드로 5분 만에 확인해요", font(38, 600), CREAM, (0, 0, 0, 170), 2, 6, "mm")
    text(img, (545, 1688), "깐밤AI", font(48, 700), CREAM, (40, 20, 5, 150), 1, 3, "mm", 1)
    text(img, (W // 2, 1790), "@kkanbam.ai", font(32, 500), CREAM, (0, 0, 0, 170), 2, 6, "mm", 1)

    img.convert("RGB").save(out_path, "PNG")
    print("STORY_IMAGE", out_path)

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) > 1 else 1)
    main(*sys.argv[1:4])
