import json, sys, time, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
OLD = "qx0gmmxgi2E"
h = {"Authorization": f"Bearer {access_token()}", "Content-Type": "application/json"}
body = json.dumps({"id": OLD, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "embeddable": True, "publicStatsViewable": True, "license": "youtube"}}).encode()
try:
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status", data=body, method="PUT", headers=h), timeout=60); print("SET", r.status)
except urllib.error.HTTPError as e: print("ERR", e.code, e.read().decode()[:300])
for k in range(3):
    time.sleep(6)
    v = json.load(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status&id=" + OLD, headers=h), timeout=60))
    print("READ", [(i["status"]["privacyStatus"], i["status"].get("publishAt")) for i in v["items"]], flush=True)
