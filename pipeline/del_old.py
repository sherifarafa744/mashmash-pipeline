import json, sys, urllib.request, urllib.error, datetime
sys.path.insert(0, "pipeline")
from upload import access_token
h = {"Authorization": f"Bearer {access_token()}"}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60))
NEW = "LRbVtHteJ0g"
body = json.dumps({"id": NEW, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}).encode()
try:
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status", data=body, method="PUT", headers={**h, "Content-Type": "application/json"}), timeout=60)
    print("UPDATED", r.status, datetime.datetime.now(datetime.timezone.utc).isoformat())
except urllib.error.HTTPError as e:
    print("UPDERR", e.code, e.read().decode()[:300]); sys.exit(1)
v = get(f"https://www.googleapis.com/youtube/v3/videos?part=status,snippet&id={NEW}")
print("VID", [(i["status"]["privacyStatus"], i["status"].get("publishAt"), i["snippet"].get("publishedAt")) for i in v["items"]])
