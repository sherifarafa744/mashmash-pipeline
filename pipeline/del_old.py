import json, sys, time, urllib.request, urllib.error, datetime
sys.path.insert(0, "pipeline")
from upload import access_token
NEW = "qx0gmmxgi2E"
def hdr(): return {"Authorization": f"Bearer {access_token()}"}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=hdr()), timeout=60))
def show(tag):
    v = get(f"https://www.googleapis.com/youtube/v3/videos?part=status,snippet&id={NEW}")
    print(tag, [(i["status"]["privacyStatus"], i["status"].get("publishAt"), i["snippet"].get("publishedAt")) for i in v["items"]], datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)
show("BEFORE")
t = datetime.datetime(2026, 11, 27, 17, 59, 53, tzinfo=datetime.timezone.utc).timestamp()
w = t - time.time(); print("sleep", int(w), flush=True)
if w > 0: time.sleep(w)
body = json.dumps({"id": NEW, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True, "publicStatsViewable": True, "license": "youtube"}}).encode()
try:
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status", data=body, method="PUT", headers={**hdr(), "Content-Type": "application/json"}), timeout=60)
    print("SET public", r.status, datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)
except urllib.error.HTTPError as e:
    print("SETERR", e.code, e.read().decode()[:300], flush=True)
time.sleep(5); show("AFTER")
