import json, sys, urllib.request
sys.path.insert(0, "pipeline")
from upload import access_token
tok = access_token()
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": f"Bearer {tok}"}), timeout=60))
d = get("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,status&maxResults=50&playlistId=PLM9buLI-Epxo")
ids = [i["snippet"]["resourceId"]["videoId"] for i in d["items"]]
v = get("https://www.googleapis.com/youtube/v3/videos?part=status,snippet&id=" + ",".join(ids))
print("PLAYLIST", json.dumps([(i["id"], i["snippet"]["title"][:40], i["status"]["privacyStatus"], i["status"].get("publishAt")) for i in v["items"]], ensure_ascii=False))
