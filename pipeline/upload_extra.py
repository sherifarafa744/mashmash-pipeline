"""One-off extra Short (user-approved video, uploaded unchanged): upload PRIVATE with no publishAt,
set thumbnail, sleep to the slot, flip public, post the channel question comment.
Env: PUBLISH_AT (ISO UTC), VIDEO, THUMB, TITLE, DESC_FILE, COMMENT, DRY=1 to print only."""
import json, os, pathlib, sys, time, datetime as dt, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from upload import access_token

ROOT = pathlib.Path(__file__).resolve().parent.parent
title = os.environ["TITLE"]; desc = pathlib.Path(os.environ["DESC_FILE"]).read_text().strip()
at = os.environ["PUBLISH_AT"]; video_path = ROOT / os.environ["VIDEO"]; thumb = ROOT / os.environ["THUMB"]
tags = ["بسبوسة", "قطة حزينة", "قصص قطط", "قطط", "حكايات بسبوسة", "كرتون", "قصة مؤثرة", "شورتس", "Shorts", "Basbusa"]
status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
meta = {"snippet": {"title": title, "description": desc, "categoryId": "24", "tags": tags}, "status": status}
print(json.dumps(meta, ensure_ascii=False, indent=1))
if os.environ.get("DRY") == "1":
    sys.exit(0)

def call(req, timeout=120):
    return urllib.request.urlopen(req, timeout=timeout)

video = video_path.read_bytes()
tok = access_token()
try:
    init = urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(video))})
    uri = call(init, 60).headers["Location"]
except Exception as e:
    print("init with containsSyntheticMedia failed:", e, getattr(e, "read", lambda: b"")()[:300])
    status.pop("containsSyntheticMedia"); meta["status"] = status
    init = urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(video))})
    uri = call(init, 60).headers["Location"]
    print("WARNING: uploaded WITHOUT the synthetic-media disclosure flag")
vid = json.load(call(urllib.request.Request(uri, data=video, method="PUT", headers={"Content-Type": "video/mp4"}), 600))["id"]
print("uploaded PRIVATE:", f"https://youtu.be/{vid}", flush=True)
try:
    call(urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}", data=thumb.read_bytes(),
        method="POST", headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"}))
    print("custom thumbnail set", flush=True)
except Exception as e:
    print("thumbnail failed (non-fatal):", e)

t = dt.datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp() - 6
wait = t - time.time()
print(f"HOLD: {vid} stays private, flipping public in {max(0, wait):.0f}s", flush=True)
if wait > 0:
    time.sleep(wait)
for attempt in range(5):
    try:
        tok = access_token()
        st = {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True, "publicStatsViewable": True, "license": "youtube"}
        if "containsSyntheticMedia" in status:
            st["containsSyntheticMedia"] = True
        r = call(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status",
            data=json.dumps({"id": vid, "status": st}).encode(), method="PUT",
            headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}), 60)
        print("FLIPPED public", r.status, dt.datetime.now(dt.timezone.utc).isoformat(), flush=True)
        time.sleep(5)
        j = json.load(call(urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?part=status&id={vid}",
            headers={"Authorization": f"Bearer {tok}"}), 60))["items"][0]["status"]
        print("STATUS", j.get("privacyStatus"), "synthetic:", j.get("containsSyntheticMedia"), flush=True)
        break
    except Exception as e:
        print("flip retry", attempt, e, getattr(e, "read", lambda: b"")()[:300], flush=True); time.sleep(10)
else:
    raise SystemExit("FLIP FAILED: video left private")
try:
    body = json.dumps({"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": os.environ["COMMENT"]}}}}).encode()
    r = call(urllib.request.Request("https://www.googleapis.com/youtube/v3/commentThreads?part=snippet", data=body, method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}), 60)
    print("posted channel comment:", json.load(r)["id"])
except Exception as e:
    print("comment failed (video is live regardless):", e)
