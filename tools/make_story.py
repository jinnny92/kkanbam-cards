"""깐밤AI "오늘 게시물 올라왔어요" 홍보용 인스타 스토리 이미지 (1080x1920 PNG).

usage:
  python3 make_story.py <표지 PNG> <출력 PNG> "<날짜 라벨, 예: 10월 24일 토요일>"
    -> render_cards.py 와 같은 색·폰트로, 위쪽 제목 / 가운데 기울인 표지 카드 / 아래쪽 안내 문구를 배치한다.
       스토리 안전 영역: 위아래 250px 안에는 글자를 두지 않는다.
"""
import base64, html, pathlib, sys
from playwright.sync_api import sync_playwright

if len(sys.argv) != 4:
    raise SystemExit('usage: make_story.py <cover.png> <out.png> "<날짜 라벨>"')
src, out, label = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
if not src.is_file():
    raise SystemExit(f"cover not found: {src}")
out.parent.mkdir(parents=True, exist_ok=True)

A, BG, FG, SUB, MUT = "#F2C14E", "#0D1530", "#F4F5F7", "#D5D9E0", "#9AA1AC"  # render_cards.py 와 동일
FONT = "'Noto Sans CJK KR','Noto Sans KR',sans-serif"
e = lambda s: html.escape(s).replace("\n", "<br>")
img = "data:image/png;base64," + base64.b64encode(src.read_bytes()).decode()
CW = 760  # 표지 카드 가로(px); 1080x1350 비율 유지

body = f"""
<div style="width:1080px;height:1920px;box-sizing:border-box;padding:250px 90px;background:{BG};color:{FG};
  font-family:{FONT};display:flex;flex-direction:column;align-items:center;justify-content:space-between;position:relative;overflow:hidden">
  <div style="position:absolute;top:-260px;right:-220px;width:720px;height:720px;border-radius:50%;
    background:radial-gradient(circle, rgba(242,193,78,.16), rgba(242,193,78,0) 70%)"></div>
  <div style="align-self:stretch;display:flex;flex-direction:column;gap:18px;text-align:center">
    <div style="font-size:30px;font-weight:700;color:{A};letter-spacing:1px">NEW · {e(label)}</div>
    <h1 style="margin:0;font-size:80px;font-weight:900;line-height:1.18;letter-spacing:-2.5px">오늘의 AI 소식<br>올라왔어요 <span style="font-size:.78em">🌙</span></h1>
  </div>
  <div style="flex-shrink:0;display:flex;align-items:center;justify-content:center">
    <img src="{img}" style="width:{CW}px;height:{CW * 1350 // 1080}px;display:block;border-radius:36px;transform:rotate(-2deg);
      box-shadow:0 30px 70px rgba(0,0,0,.55), 0 0 0 3px rgba(244,245,247,.16)">
  </div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:22px;text-align:center">
    <div style="font-size:36px;font-weight:700;color:{SUB}">피드에서 카드로 5분 만에 확인해요 👉</div>
    <div style="padding:14px 34px;border-radius:999px;background:{A};color:{BG};font-size:32px;font-weight:900">@kkanbam.ai</div>
  </div>
</div>"""

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.set_content(f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><style>body{{margin:0;word-break:keep-all}}</style></head><body>{body}</body></html>")
    pg.wait_for_timeout(200)
    pg.screenshot(path=str(out))
    b.close()
print("STORY_IMAGE", out)
