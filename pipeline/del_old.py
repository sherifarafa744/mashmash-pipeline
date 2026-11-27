import json, sys, urllib.request
sys.path.insert(0, "pipeline")
from upload import access_token
h = {"Authorization": f"Bearer {access_token()}"}
B = "https://www.googleapis.com/youtube/v3/"
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60))
v = get(B + "videos?part=status&id=tyxgV1mJmP0")["items"][0]; print("AFTER", v["status"]["privacyStatus"], v["status"].get("publishAt"))
for p in get(B + "playlists?part=snippet&mine=true&maxResults=50")["items"]:
    sn = p["snippet"]; t = sn["title"]
    new = {"PLM9buLI-Epxo": "حكاية مصباح بسبوسة السحري | حكايات بسبوسة | الموسم 1", "PLFeKx89Tl-dg": "حكاية كنز جزيرة التونة الذهبية | حكايات بسبوسة | الموسم 1"}.get(p["id"])
    if new:
        body = {"id": p["id"], "snippet": {"title": new, "description": "كل أجزاء الحكاية بالترتيب من الجزء الأول. كرتون عربي بالعامية المصرية، حكايات قطط."}}
        r = urllib.request.urlopen(urllib.request.Request(B + "playlists?part=snippet", data=json.dumps(body).encode(), method="PUT", headers={**h, "Content-Type": "application/json"}), timeout=60)
        print("RENAMED", p["id"], r.status)
for p in get(B + "playlists?part=snippet&mine=true&maxResults=50")["items"]: print("PL", p["id"], p["snippet"]["title"])
