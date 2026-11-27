import json, sys, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
h = {"Authorization": f"Bearer {access_token()}"}
B = "https://www.googleapis.com/youtube/v3/"
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60))
def put(u, body):
    return urllib.request.urlopen(urllib.request.Request(B + u, data=json.dumps(body).encode(), method="PUT", headers={**h, "Content-Type": "application/json"}), timeout=60).status
VID = "tyxgV1mJmP0"
ep = json.load(open("episodes/arc2/ep4.json"))
v = get(B + "videos?part=snippet,status&id=" + VID)["items"][0]
sn = v["snippet"]; lines = sn["description"].split("\n")
print("BEFOREDESC", repr(sn["description"][:300]))
lines[0] = "كرتون عربي بالعامية المصرية، حكايات قطط: الجزء 4 من حكايات بسبوسة"
lines[-1] = "#Shorts #كرتون_مصري #رسوم_متحركة #حكايات_بسبوسة"
sn["description"] = "\n".join(lines)
print("UPD", put("videos?part=snippet", {"id": VID, "snippet": {k: sn[k] for k in ("title", "description", "categoryId", "tags") if k in sn}}))
print("UPD2", put("videos?part=status", {"id": VID, "status": {"privacyStatus": "private", "publishAt": "2026-11-27T18:00:00.000Z", "selfDeclaredMadeForKids": False}}))
v = get(B + "videos?part=snippet,status&id=" + VID)["items"][0]
print("AFTER", v["status"]["privacyStatus"], v["status"].get("publishAt"), v["snippet"]["title"], v["snippet"]["tags"]); print("DESC", repr(v["snippet"]["description"]))
pls = get(B + "playlists?part=snippet,contentDetails&mine=true&maxResults=50")["items"]
for p in pls:
    print("PL", p["id"], p["snippet"]["title"], p["contentDetails"]["itemCount"])
    items = get(B + "playlistItems?part=snippet&maxResults=50&playlistId=" + p["id"])["items"]
    for i in items: print("  ITEM", i["snippet"]["position"], i["snippet"]["resourceId"]["videoId"], i["snippet"]["title"][:50])
