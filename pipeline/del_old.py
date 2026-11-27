import json, sys, time, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
NEW = "N_asSQ7OLhQ"
h = {"Authorization": f"Bearer {access_token()}", "Content-Type": "application/json"}
g = lambda u: json.load(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/"+u, headers=h), timeout=60))
it = g("videos?part=snippet&id="+NEW)["items"][0]["snippet"]
lines = it["description"].split("\n")
lines[0] = "بسبوسة فتحت الصندوق والعقرب هرب، بس صوت غريب بدأ يطلع من جواه!"
tags = ["Shorts","بسبوسة","بسبوس","قصص بسبوس","مسلسل بسبوس","حكايات","حكايات بسبوسة","شورتس","قصص قطط","قطط"]
body = json.dumps({"id": NEW, "snippet": {"title": it["title"], "description": "\n".join(lines), "tags": tags, "categoryId": it["categoryId"]}}).encode()
try:
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=snippet", data=body, method="PUT", headers=h), timeout=60); print("SNIP", r.status)
except urllib.error.HTTPError as e: print("ERR", e.code, e.read().decode()[:300])
time.sleep(8)
x = g("videos?part=snippet,status&id="+NEW)["items"][0]
print("NEWDESC", x["snippet"]["description"].split("\n")[:2], x["status"]["privacyStatus"], x["snippet"].get("tags"))
for i in g("playlistItems?part=snippet&maxResults=50&playlistId=PLM9buLI-Epxo")["items"]: print("PL", i["snippet"]["position"], i["snippet"]["resourceId"]["videoId"])
