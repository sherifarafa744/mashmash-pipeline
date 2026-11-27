import json, sys, time, urllib.request, urllib.error, datetime
sys.path.insert(0, "pipeline")
from upload import access_token
NEW = "LRbVtHteJ0g"
def hdr(): return {"Authorization": f"Bearer {access_token()}"}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=hdr()), timeout=60))
def setp(p):
    body = json.dumps({"id": NEW, "status": {"privacyStatus": p, "selfDeclaredMadeForKids": False}}).encode()
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status", data=body, method="PUT", headers={**hdr(), "Content-Type": "application/json"}), timeout=60)
    print("SET", p, r.status, datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)
def show(tag):
    v = get(f"https://www.googleapis.com/youtube/v3/videos?part=status,snippet&id={NEW}")
    print(tag, [(i["status"]["privacyStatus"], i["status"].get("publishAt"), i["snippet"].get("publishedAt")) for i in v["items"]], flush=True)
setp("private"); time.sleep(5); show("PRIVATE")
t = datetime.datetime(2026, 11, 27, 14, 59, 52, tzinfo=datetime.timezone.utc).timestamp()
w = t - time.time(); print("sleep", int(w), flush=True)
if w > 0: time.sleep(w)
setp("public"); time.sleep(5); show("PUBLIC")
