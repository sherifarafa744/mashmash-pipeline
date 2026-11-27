import json, sys, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
tok = access_token(); h = {"Authorization": f"Bearer {tok}"}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60))
try:
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?id=Y_hJxEtPB8o", method="DELETE", headers=h), timeout=60)
    print("DELETED", r.status)
except urllib.error.HTTPError as e:
    print("ERR", e.code, e.read().decode()[:300])
for vid in ("Y_hJxEtPB8o", "g5LH-Zz_Lu4"):
    v = get(f"https://www.googleapis.com/youtube/v3/videos?part=status&id={vid}")
    print(vid, [(i["status"]["privacyStatus"], i["status"].get("publishAt")) for i in v["items"]])
p = get("https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&playlistId=PLM9buLI-Epxo")
print("PLAYLIST", [i["contentDetails"]["videoId"] for i in p["items"]])
