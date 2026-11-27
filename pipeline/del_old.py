import json, sys, urllib.request, urllib.error, datetime
sys.path.insert(0, "pipeline")
from upload import access_token
h = {"Authorization": f"Bearer {access_token()}"}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60))
NEW = "LRbVtHteJ0g"
def show(tag):
    v = get(f"https://www.googleapis.com/youtube/v3/videos?part=status,snippet&id={NEW}")
    print(tag, [(i["status"]["privacyStatus"], i["status"].get("publishAt"), i["snippet"].get("publishedAt")) for i in v["items"]], datetime.datetime.now(datetime.timezone.utc).isoformat())
    return v["items"][0]["status"]
st = show("BEFORE")
if st["privacyStatus"] != "private" or st.get("publishAt") != "2026-11-27T15:00:00Z":
    body = json.dumps({"id": NEW, "status": {"privacyStatus": "private", "publishAt": "2026-11-27T15:00:00.000Z", "selfDeclaredMadeForKids": False}}).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status", data=body, method="PUT", headers={**h, "Content-Type": "application/json"}), timeout=60)
        print("REVERT", r.status)
    except urllib.error.HTTPError as e:
        print("REVERTERR", e.code, e.read().decode()[:300])
import time; time.sleep(8)
show("AFTER")
