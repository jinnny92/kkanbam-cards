"""깐밤AI Instagram carousel + story poster.

Credentials come from ~/.kkanbam/.env (never committed, never printed):
  INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID, INSTAGRAM_API_BASE (optional)

usage:
  python3 ig_post.py check                      -> prints POSTED_TODAY <permalink> if a carousel (CAROUSEL_ALBUM) exists for today (Asia/Seoul), else NOT_POSTED
  python3 ig_post.py post <YYYY-MM-DD> <caption.txt>
        -> uses cards/<date>/*.png from this repo (must already be pushed), creates carousel, publishes, prints PUBLISHED <id> <permalink>
  python3 ig_post.py story-check                -> prints STORY_POSTED_TODAY <id> if a story exists for today (Asia/Seoul), else STORY_NOT_POSTED
  python3 ig_post.py story <image repo-relative path> [--force]
        -> image must already be pushed to main (e.g. cards/<date>/story.png; make it with make_story.py).
           Skips with STORY_POSTED_TODAY <id> unless --force. Creates STORIES container (image_url),
           waits for FINISHED, publishes, prints STORY_PUBLISHED <id>
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error, pathlib, datetime

ENV = pathlib.Path(os.path.expanduser("~/.kkanbam/.env"))
env = dict(l.split("=", 1) for l in ENV.read_text().splitlines() if "=" in l)
TOKEN = env["INSTAGRAM_ACCESS_TOKEN"].strip()
UID = env["INSTAGRAM_USER_ID"].strip()
BASE = env.get("INSTAGRAM_API_BASE", "https://graph.instagram.com/v24.0").strip()
REPO = pathlib.Path(__file__).resolve().parent.parent
RAW_ROOT = "https://raw.githubusercontent.com/jinnny92/kkanbam-cards/main"
RAW = f"{RAW_ROOT}/cards"
KST = datetime.timezone(datetime.timedelta(hours=9))


def call(method, path, **params):
    params["access_token"] = TOKEN
    q = urllib.parse.urlencode(params)
    url = f"{BASE}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{q}")
    else:
        req = urllib.request.Request(url, data=q.encode(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"API error {e.code}: {e.read().decode().replace(TOKEN, '***')}")
    except urllib.error.URLError as e:
        raise SystemExit(f"network error: {str(e.reason).replace(TOKEN, '***')}")


def wait_ready(cid):
    for _ in range(40):
        s = call("GET", cid, fields="status_code").get("status_code")
        if s == "FINISHED":
            return
        if s in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container {cid} {s}")
        time.sleep(3)
    raise SystemExit(f"container {cid} timeout")


def _today_media(match):
    today = datetime.datetime.now(KST).date()
    for m in call("GET", f"{UID}/media", fields="timestamp,permalink,media_type,media_product_type", limit="10").get("data", []):
        ts = datetime.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z").astimezone(KST)
        if ts.date() == today and match(m):
            return m["permalink"]
    return None


def posted_today():  # carousels only, so other media types are never mistaken for today's cards
    return _today_media(lambda m: m.get("media_type") == "CAROUSEL_ALBUM")


def story_posted_today():
    today = datetime.datetime.now(KST).date()
    for m in call("GET", f"{UID}/stories", fields="id,timestamp").get("data", []):
        ts = datetime.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z").astimezone(KST)
        if ts.date() == today:
            return m["id"]
    return None


cmd = sys.argv[1]
if cmd == "check":
    p = posted_today()
    print(f"POSTED_TODAY {p}" if p else "NOT_POSTED")
elif cmd == "post":
    date, cap = sys.argv[2], pathlib.Path(sys.argv[3]).read_text().strip()
    p = posted_today()
    if p:
        print(f"POSTED_TODAY {p}")
        sys.exit(0)
    files = sorted((REPO / "cards" / date).glob("*.png"))[:10]
    if len(files) < 2:
        raise SystemExit(f"need >=2 cards in cards/{date}, found {len(files)}")
    children = []
    for f in files:
        children.append(call("POST", f"{UID}/media", image_url=f"{RAW}/{date}/{f.name}", is_carousel_item="true")["id"])
    for c in children:
        wait_ready(c)
    car = call("POST", f"{UID}/media", media_type="CAROUSEL", children=",".join(children), caption=cap)["id"]
    wait_ready(car)
    mid = call("POST", f"{UID}/media_publish", creation_id=car)["id"]
    print("PUBLISHED", mid, call("GET", mid, fields="permalink").get("permalink"))
elif cmd == "story-check":
    sid = story_posted_today()
    print(f"STORY_POSTED_TODAY {sid}" if sid else "STORY_NOT_POSTED")
elif cmd == "story":
    args = [a for a in sys.argv[2:] if a != "--force"]
    force = "--force" in sys.argv[2:]
    if len(args) != 1:
        raise SystemExit("usage: ig_post.py story <image repo-relative path> [--force]")
    rel = args[0].strip("/")
    if not (REPO / rel).is_file():
        raise SystemExit(f"image not found in repo: {rel}")
    if not force:
        sid = story_posted_today()
        if sid:
            print(f"STORY_POSTED_TODAY {sid}")
            sys.exit(0)
    image_url = f"{RAW_ROOT}/{urllib.parse.quote(rel)}"
    cid = call("POST", f"{UID}/media", media_type="STORIES", image_url=image_url)["id"]
    wait_ready(cid)
    mid = call("POST", f"{UID}/media_publish", creation_id=cid)["id"]
    print("STORY_PUBLISHED", mid)
else:
    raise SystemExit(f"unknown command: {cmd}")
