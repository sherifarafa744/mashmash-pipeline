import json, sys, time, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
OLD, NEW = "qx0gmmxgi2E", "N_asSQ7OLhQ"
h = {"Authorization": f"Bearer {access_token()}"}
def g(u): return json.load(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/"+u, headers=h), timeout=60))
try:
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?id="+OLD, method="DELETE", headers=h), timeout=60); print("DELETED", r.status)
except urllib.error.HTTPError as e: print("ERR", e.code, e.read().decode()[:300])
time.sleep(8)
print("OLDCOUNT", len(g("videos?part=id&id="+OLD)["items"]))
for it in g("videos?part=snippet,status&id="+NEW)["items"]:
    print("NEW", it["status"]["privacyStatus"], it["status"].get("publishAt"), it["snippet"]["publishedAt"], it["snippet"]["title"])
    print("DESC", it["snippet"]["description"].replace("\n", " | "))
    print("TAGS", it["snippet"].get("tags"))
ch = g("channels?part=contentDetails&mine=true")["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
ids = [i["contentDetails"]["videoId"] for i in g("playlistItems?part=contentDetails&maxResults=50&playlistId="+ch)["items"]]
for it in g("videos?part=snippet,status&id="+",".join(ids))["items"]:
    if "الجزء 4" in it["snippet"]["title"] or "ج4" in it["snippet"]["title"] or it["status"]["privacyStatus"] != "public": print("UP", it["id"], it["status"]["privacyStatus"], it["snippet"]["title"][:50])
for i in g("playlistItems?part=snippet&maxResults=50&playlistId=PLM9buLI-Epxo")["items"]: print("PL", i["snippet"]["position"], i["snippet"]["resourceId"]["videoId"])
