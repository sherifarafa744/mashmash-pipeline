import json, sys, urllib.request
sys.path.insert(0, "pipeline")
from upload import access_token
h = {"Authorization": f"Bearer {access_token()}"}
g = lambda u: json.load(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/"+u, headers=h), timeout=60))
for v in ("N_asSQ7OLhQ", "LRbVtHteJ0g", "g5LH-Zz_Lu4"):
    it = g("videos?part=snippet,status&id="+v)["items"][0]
    print("TH", v, json.dumps(it["snippet"]["thumbnails"].get("maxres") or it["snippet"]["thumbnails"].get("high")), it["status"]["uploadStatus"])
