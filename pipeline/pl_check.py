import json, sys, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
tok = access_token()
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": f"Bearer {tok}"}), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:400]}
d = get("https://www.googleapis.com/youtube/v3/playlists?part=snippet&mine=true&maxResults=50")
print(json.dumps(d if "error" in d else [(i["id"], i["snippet"]["title"]) for i in d["items"]], ensure_ascii=False))
for pid in ("PLM9buLI-Epxo", "PLFeKx89Tl-dg"):
    d = get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={pid}")
    print(pid, json.dumps(d if "error" in d else [i["snippet"]["resourceId"]["videoId"] for i in d["items"]]))
