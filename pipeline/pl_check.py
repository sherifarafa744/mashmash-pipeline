import json, sys, urllib.request
sys.path.insert(0, "pipeline")
from upload import access_token
tok = access_token()
h = {"Authorization": f"Bearer {tok}"}
d = json.load(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=PLM9buLI-Epxo", headers=h), timeout=60))
for i in d["items"]:
    if i["snippet"]["resourceId"]["videoId"] == "Pkbs9jL3Kw8":
        r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/playlistItems?id=" + i["id"], method="DELETE", headers=h), timeout=60)
        print("REMOVED old from playlist", r.status)
d = json.load(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=PLM9buLI-Epxo", headers=h), timeout=60))
print("NOW", [i["snippet"]["resourceId"]["videoId"] for i in d["items"]])
