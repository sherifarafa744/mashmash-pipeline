import json, sys, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
tok = access_token(); h = {"Authorization": f"Bearer {tok}"}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60))
NEW, OLD = "LRbVtHteJ0g", "aq4mFe844F0"
body = json.dumps({"id": NEW, "status": {"privacyStatus": "private", "publishAt": "2026-11-27T15:00:00.000Z", "selfDeclaredMadeForKids": False}}).encode()
try:
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status", data=body, method="PUT", headers={**h, "Content-Type": "application/json"}), timeout=60)
    print("UPDATED", r.status)
except urllib.error.HTTPError as e:
    print("UPDERR", e.code, e.read().decode()[:300]); sys.exit(1)
v = get(f"https://www.googleapis.com/youtube/v3/videos?part=status&id={NEW}")
st = v["items"][0]["status"]; print("NEWSTATUS", st.get("privacyStatus"), st.get("publishAt"))
if st.get("publishAt", "").startswith("2026-11-27T15:00"):
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?id={OLD}", method="DELETE", headers=h), timeout=60)
        print("DELETED", r.status)
    except urllib.error.HTTPError as e:
        print("ERR", e.code, e.read().decode()[:300])
for vid in (OLD, NEW):
    v = get(f"https://www.googleapis.com/youtube/v3/videos?part=status&id={vid}")
    print(vid, [(i["status"]["privacyStatus"], i["status"].get("publishAt")) for i in v["items"]])
