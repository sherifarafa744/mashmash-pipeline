import json, sys, urllib.request, urllib.error, urllib.parse
sys.path.insert(0, "pipeline")
from upload import access_token
h = {"Authorization": f"Bearer {access_token()}"}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60))
B = "https://www.googleapis.com/youtube/v3/"
up = get(B + "channels?part=contentDetails&mine=true")["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
ids, tok = [], None
while True:
    d = get(B + f"playlistItems?part=contentDetails&maxResults=50&playlistId={up}" + (f"&pageToken={tok}" if tok else ""))
    ids += [i["contentDetails"]["videoId"] for i in d["items"]]
    tok = d.get("nextPageToken")
    if not tok: break
print("TOTAL", len(ids))
BAD = "قصص اطفال"
for i in range(0, len(ids), 50):
    for v in get(B + "videos?part=snippet,status&id=" + ",".join(ids[i:i+50]))["items"]:
        sn = v["snippet"]; tags = sn.get("tags", [])
        if BAD not in tags:
            print("OK-NOTAG", v["id"], v["status"]["privacyStatus"]); continue
        sn["tags"] = [t for t in tags if t != BAD] + ([] if "حكايات" in tags else ["حكايات"])
        body = json.dumps({"id": v["id"], "snippet": {k: sn[k] for k in ("title", "description", "categoryId", "tags", "defaultLanguage", "defaultAudioLanguage") if k in sn}}).encode()
        try:
            r = urllib.request.urlopen(urllib.request.Request(B + "videos?part=snippet", data=body, method="PUT", headers={**h, "Content-Type": "application/json"}), timeout=60)
            print("FIXED", v["id"], v["status"]["privacyStatus"], r.status)
        except urllib.error.HTTPError as e:
            print("ERR", v["id"], e.code, e.read().decode()[:200])
for i in range(0, len(ids), 50):
    for v in get(B + "videos?part=snippet,status&id=" + ",".join(ids[i:i+50]))["items"]:
        print("CHECK", v["id"], v["status"]["privacyStatus"], BAD in v["snippet"].get("tags", []), v["snippet"]["title"][:40])
