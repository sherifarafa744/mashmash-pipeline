import json, sys, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
tok = access_token(); h = {"Authorization": f"Bearer {tok}"}
for i in ("qx0gmmxgi2E","tyxgV1mJmP0"):
    v = json.load(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=snippet,status&id="+i, headers=h), timeout=60))
    for it in v["items"]:
        print(i, json.dumps({"title":it["snippet"]["title"],"desc":it["snippet"]["description"],"tags":it["snippet"].get("tags"),"cat":it["snippet"]["categoryId"],"st":it["status"]}, ensure_ascii=False))
