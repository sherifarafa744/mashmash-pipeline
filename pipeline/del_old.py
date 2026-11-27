import json, sys, urllib.request
sys.path.insert(0, "pipeline")
from upload import access_token
h = {"Authorization": f"Bearer {access_token()}"}
def g(u): return json.load(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/"+u,headers=h),timeout=60))
ch=g("channels?part=contentDetails&mine=true")["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
ids=[i["contentDetails"]["videoId"] for i in g("playlistItems?part=contentDetails&maxResults=50&playlistId="+ch)["items"]]
for it in g("videos?part=snippet,status&id="+",".join(ids))["items"]:
    print("UP",it["id"],it["status"]["privacyStatus"],it["status"].get("publishAt"),it["snippet"]["title"][:50])
for p in ("PLM9buLI-Epxo",):
    for i in g("playlistItems?part=snippet&maxResults=50&playlistId="+p)["items"]: print("PL",p,i["snippet"]["position"],i["snippet"]["resourceId"]["videoId"],i["snippet"]["title"][:40])
