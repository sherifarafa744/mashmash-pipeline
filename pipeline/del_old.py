import json, sys, urllib.request
sys.path.insert(0, "pipeline")
from upload import access_token
h = {"Authorization": f"Bearer {access_token()}"}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60))
for vid in ("aq4mFe844F0", "LRbVtHteJ0g", "g5LH-Zz_Lu4"):
    v = get(f"https://www.googleapis.com/youtube/v3/videos?part=status&id={vid}")
    print("VID", vid, [(i["status"]["privacyStatus"], i["status"].get("publishAt")) for i in v["items"]])
p = get("https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&playlistId=PLM9buLI-Epxo")
print("PLAYLIST", [i["contentDetails"]["videoId"] for i in p["items"]])
