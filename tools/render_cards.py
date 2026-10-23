import json, sys, html, pathlib
from playwright.sync_api import sync_playwright

d = json.loads(pathlib.Path(sys.argv[1]).read_text())
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
A, BG, FG, SUB, MUT = "#F2C14E", "#0D1530", "#F4F5F7", "#D5D9E0", "#9AA1AC"
e = lambda s: html.escape(s).replace("\n", "<br>")

def icons(s, gap=2):
    return (f'<span style="display:flex;align-items:center;gap:{gap}px">'
        f'<svg width="{s}" height="{s}" viewBox="0 0 24 24"><path d="M20.5 14.2A8.5 8.5 0 1 1 9.8 3.5a7 7 0 0 0 10.7 10.7z" fill="{A}"/></svg>'
        f'<svg width="{s}" height="{s}" viewBox="0 0 24 24"><path d="M12 2.5C8.2 5.6 4 9.6 4 14.3 4 18.4 7.6 21 12 21s8-2.6 8-6.7c0-4.7-4.2-8.7-8-11.8z" fill="#C47B3E"/>'
        f'<path d="M4.6 16.6C6.4 18.4 9 19.2 12 19.2s5.6-.8 7.4-2.6C18.4 19.4 15.5 21 12 21s-6.4-1.6-7.4-4.4z" fill="#F3D9A4"/>'
        f'<path d="M9.2 8.6C8 9.8 7.3 11.2 7.1 12.6" stroke="#E2A56B" stroke-width="1.4" stroke-linecap="round" fill="none"/></svg></span>')

logo = f'<div style="display:flex;align-items:center;gap:10px;font-weight:700;color:{FG}">{icons(28)}<span>깐밤AI</span></div>'
news, xs = d["news"], d.get("x", [])
total = 1 + len(news) + len(xs) + 1

def frame(n, inner, top_left=True, gap=40):
    tl = f'<div style="display:flex;align-items:center;gap:14px">{logo}<span>{d["short_date"]}</span></div>' if top_left else '<div></div>'
    return (f'<div style="width:1080px;height:1350px;box-sizing:border-box;padding:110px 100px;background:{BG};color:{FG};'
        f"font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif;display:flex;flex-direction:column;gap:{gap}px\">"
        f'<div style="display:flex;justify-content:space-between;align-items:center;font-size:24px;font-weight:500;color:{MUT}">{tl}<div>{n:02d} / {total:02d}</div></div>'
        f'{inner}</div>')

def block(label, text):
    return (f'<div style="display:flex;flex-direction:column;gap:12px"><div style="font-size:26px;font-weight:700;color:{A}">{label}</div>'
        f'<p style="margin:0;font-size:34px;line-height:1.65;color:{SUB}">{e(text)}</p></div>')

def story(n, it, chip, why_label):
    title = it["title"]
    size = 64 if max(len(l) for l in title.split("\n")) <= 14 else 54
    inner = (f'<div style="display:flex;flex-direction:column;gap:24px">{chip}'
        f'<h2 style="margin:0;font-size:{size}px;font-weight:900;line-height:1.25;letter-spacing:-1.5px">{e(title)}</h2></div>'
        + block("무슨 일?", it["what"]) + block(why_label, it["why"])
        + f'<div style="margin-top:auto;font-size:22px;color:{MUT}">출처: {e(it["source"])}</div>')
    return frame(n, inner)

pages = []
items = "".join(f'<div style="display:flex;gap:20px"><span style="font-weight:900;color:{A}">{i}</span><span>{e(it["short"])}</span></div>' for i, it in enumerate(news, 1))
extra = "+ X에서 뜨는 화제" if xs else ""
pages.append(frame(1,
    f'<div style="display:flex;flex-direction:column;gap:20px"><div style="font-size:30px;font-weight:700;color:{A}">{e(d["date_label"])}</div>'
    f'<h1 style="margin:0;font-size:120px;font-weight:900;line-height:1.12;letter-spacing:-3px">간밤의<br>AI 소식</h1></div>'
    f'<div style="font-size:32px;font-weight:500;color:{SUB};margin-top:-24px">자는 동안 일어난 AI 이야기, 5분 요약</div>'
    f'<div style="display:flex;flex-direction:column;gap:28px;font-size:34px;font-weight:500;line-height:1.4;color:{SUB}">{items}</div>'
    f'<div style="margin-top:auto;display:flex;justify-content:space-between;font-size:24px;color:{MUT}"><div>{extra}</div>'
    f'<div style="font-weight:700;color:{FG}">옆으로 넘겨 보세요 →</div></div>', top_left=False).replace("<div></div>", logo, 1))
n = 2
for it in news:
    chip = f'<div style="align-self:flex-start;padding:10px 22px;border-radius:999px;background:{A};color:{BG};font-size:24px;font-weight:700">{e(it["tag"])}</div>'
    pages.append(story(n, it, chip, "왜 중요해?")); n += 1
for it in xs:
    chip = f'<div style="align-self:flex-start;padding:8px 20px;border-radius:999px;border:2px solid {A};color:{A};font-size:24px;font-weight:700">X에서 뜨는 화제</div>'
    pages.append(story(n, it, chip, "왜 화제야?")); n += 1
pages.append(frame(n,
    f'<div style="margin-top:auto;display:flex;flex-direction:column;gap:40px">{icons(120, 8)}'
    f'<h2 style="margin:0;font-size:84px;font-weight:900;line-height:1.2;letter-spacing:-2px">오늘의 간밤 소식,<br>여기까지!</h2>'
    f'<p style="margin:0;font-size:34px;line-height:1.6;color:{SUB}">매일 아침, 자는 동안 일어난<br>AI 소식을 5분으로 정리해요.</p></div>'
    f'<div style="margin-top:auto;display:flex;gap:16px"><div style="padding:18px 32px;border-radius:999px;background:{A};color:{BG};font-size:28px;font-weight:700">팔로우하고 내일 아침에 또 만나요</div>'
    f'<div style="padding:18px 32px;border-radius:999px;border:2px solid {MUT};color:{FG};font-size:28px;font-weight:700">저장해두기</div></div>'
    f'<div style="font-size:24px;font-weight:700;color:{FG}">깐밤AI</div>', top_left=False))

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1350})
    for i, body in enumerate(pages, 1):
        pg.set_content(f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><style>body{{margin:0;word-break:keep-all}}</style></head><body>{body}</body></html>")
        pg.wait_for_timeout(150)
        pg.screenshot(path=str(out / f"kkanbam-ai-{d['file_date']}-{i:02d}.png"))
    b.close()
print(len(pages), "cards")
