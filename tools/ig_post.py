"""깐밤AI Instagram carousel poster.

Credentials come from ~/.kkanbam/.env (never committed, never printed):
  INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID, INSTAGRAM_API_BASE (optional)

usage:
  python3 ig_post.py check                      -> prints POSTED_TODAY <permalink> if a post exists for today (Asia/Seoul), else NOT_POSTED
  python3 ig_post.py post <YYYY-MM-DD> <caption.txt>
        -> uses cards/<date>/*.png from this repo (must already be pushed), creates carousel, publishes, prints PUBLISHED <id> <permalink>
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error, pathlib, datetime

ENV = pathlib.Path(os.path.expanduser("~/.kkanbam/.env"))
env = dict(l.split("=", 1) for l in ENV.read_text().splitlines() if "=" in l)
TOKEN = env["INSTAGRAM_ACCESS_TOKEN"].strip()
UID = env["INSTAGRAM_USER_ID"].strip()
BASE = env.get("INSTAGRAM_API_BASE", "https://graph.instagram.com/v24.0").strip()
REPO = pathlib.Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/jinnny92/kkanbam-cards/main/cards"
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


def wait_ready(cid):
    for _ in range(40):
        s = call("GET", cid, fields="status_code").get("status_code")
        if s == "FINISHED":
            return
        if s in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container {cid} {s}")
        time.sleep(3)
    raise SystemExit(f"container {cid} timeout")


def posted_today():
    today = datetime.datetime.now(KST).date()
    for m in call("GET", f"{UID}/media", fields="timestamp,permalink", limit="5").get("data", []):
        ts = datetime.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z").astimezone(KST)
        if ts.date() == today:
            return m["permalink"]
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
