# kkanbam-cards

깐밤AI(@kkanbam.ai) 인스타그램 카드뉴스 이미지 저장소.

- `cards/YYYY-MM-DD/` — 그날 게시한 카드 이미지 (1080×1350)
- `tools/render_cards.py` — data.json으로 카드 PNG 생성
- `tools/ig_post.py` — 카드로 인스타 캐러셀 게시 (토큰은 저장소 밖 `~/.kkanbam/.env`에서 읽음)

이 저장소에는 토큰·키 같은 비밀 정보를 절대 올리지 않는다.
