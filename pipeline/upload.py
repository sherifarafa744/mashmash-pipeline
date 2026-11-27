"""Upload to YouTube with the Data API resumable protocol + OAuth refresh token.

PUBLIC uploads approved by the channel owner (WhatsApp 2026-11-25).

videos.insert has its own bucket: 100 uploads/day/project (post-Jun-2026).
OAuth consent screen must be 'In production' or refresh tokens die in 7 days.
With PUBLISH_AT the video is uploaded private and scheduled (publishAt).
"""
import json, os, pathlib, sys, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import music as music_lib

def access_token() -> str:
    body = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request(
            "https://oauth2.googleapis.com/token", data=body), timeout=60) as r:
        return json.load(r)["access_token"]

def status_block() -> dict:
    """PUBLISH_AT (ISO UTC, set by the workflow) = build ahead, upload private
    and let YouTube flip it public at exactly that time. Unset = public now."""
    st = {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    at = os.environ.get("PUBLISH_AT")
    mode = os.environ.get("UPLOAD_MODE")
    if mode == "hold":  # private, NO YouTube schedule; this job flips it public at the slot
        st = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    elif at and mode != "direct":
        st = {"privacyStatus": "private", "publishAt": at, "selfDeclaredMadeForKids": False}
    return st

def main() -> None:
    ep = json.loads((ROOT / "episode.json").read_text())
    video = (ROOT / "episode_final.mp4").read_bytes()
    if os.environ.get("UPLOAD_MODE") == "direct" and os.environ.get("PUBLISH_AT"):
        # Direct public upload at slot time: wait (video is built), then upload
        # ~15s early so it is public right at the slot.
        import time, datetime as dt
        t = dt.datetime.fromisoformat(os.environ["PUBLISH_AT"].replace("Z", "+00:00")).timestamp() - 15
        wait = t - time.time()
        print(f"UPLOAD_MODE=direct: waiting {max(0, wait):.0f}s, then uploading PUBLIC", flush=True)
        if wait > 0:
            time.sleep(wait)
    if ep.get("celebration"):
        # Milestone Short: no part number, no cliffhanger, no story playlist.
        title = f"{ep['title']} | بسبوسة"
        desc = "بسبوسة بتحتفل معاكم وتشكركم على حبكم! 🎉\n"
    else:
        part = int(ep.get("part", 1) or 1)
        # Rotate the title suffix so titles do not all share one template.
        key = part + (3 if os.environ.get("ARC_DIR") == "arc2" else 0)
        fmt = [f"{{t}} | الجزء {part} | بسبوسة", f"{{t}} | بسبوسة - ج{part}", f"{{t}} - الجزء {part}",
               f"بسبوسة | {{t}} | ج{part}", f"{{t}} | حكايات بسبوسة {part}"][key % 5]
        title = fmt.format(t=ep["title"])
        desc = (ep.get("cliffhanger", "") + "\n"
                + f"الجزء {ep.get('part', 1)} من مسلسل حكايات بسبوسة (قصص بسبوس) كرتون مصري بالعامية\n")
    meta = json.dumps({"snippet": {
            "title": title,
            "description": desc + music_lib.attribution(ep.get("music") or music_lib.DEFAULT_TITLE) + "\n#حكايات_بسبوسة #كرتون_مصري #Shorts #رسوم_متحركة #قصص_بسبوسة",
            "categoryId": "24", "tags": ["بسبوسة","قصص قطط","حكايات بسبوسة","قطط","حكايات","شورتس","Shorts","قصص مصورة"]},
        "status": status_block()}).encode()
    tok = access_token()
    init = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=meta, method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(video))})
    with urllib.request.urlopen(init, timeout=60) as r:
        session_uri = r.headers["Location"]
    put = urllib.request.Request(session_uri, data=video, method="PUT",
                                 headers={"Content-Type": "video/mp4"})
    with urllib.request.urlopen(put, timeout=600) as r:
        vid = json.load(r)["id"]
    print("uploaded video:", f"https://youtu.be/{vid}")
    if not ep.get("celebration"):
        add_to_playlist(vid, tok)
        # vote.py needs the video id to count this episode's vote next run.
        state_path = ROOT / os.environ.get("STORY_STATE", "story_state.json")
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        state["last_video_id"] = vid
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    post_comment(vid, tok, ep)
    if os.environ.get("UPLOAD_MODE") == "hold" and os.environ.get("PUBLISH_AT"):
        flip_public(vid, os.environ["PUBLISH_AT"])

def flip_public(vid: str, at: str) -> None:
    """Hold-and-flip (the way part 6 went out): sleep to the slot, set public, verify."""
    import time, datetime as dt
    t = dt.datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp() - 6
    wait = t - time.time()
    print(f"HOLD: video {vid} stays private, flipping public in {max(0, wait):.0f}s", flush=True)
    if wait > 0:
        time.sleep(wait)
    for attempt in range(5):
        try:
            tok = access_token()
            body = json.dumps({"id": vid, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True, "publicStatsViewable": True, "license": "youtube"}}).encode()
            req = urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status", data=body, method="PUT",
                headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                print("FLIPPED public", r.status, dt.datetime.now(dt.timezone.utc).isoformat(), flush=True)
            time.sleep(5)
            chk = urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?part=status&id={vid}", headers={"Authorization": f"Bearer {tok}"})
            print("STATUS", json.load(urllib.request.urlopen(chk, timeout=60))["items"][0]["status"]["privacyStatus"], flush=True)
            return
        except Exception as e:
            print("flip retry", attempt, e, flush=True); time.sleep(10)
    raise SystemExit("FLIP FAILED: video left private")

def post_comment(vid: str, tok: str, ep: dict) -> None:
    """The channel asks a simple question under every new upload so viewers
    have something easy to answer. Story episodes ask the vote question (the
    answers decide the next part); celebrations ask what story viewers want.
    commentThreads.insert is covered by the youtube.force-ssl scope. Pinning
    has no API - a human pins it in Studio if wanted. Never fails the run."""
    vote = ep.get("vote") or {}
    try:
        vote_on = json.loads((ROOT / "config.json").read_text()).get("vote", True)
    except Exception:
        vote_on = True
    if not vote_on and not ep.get("celebration"):
        print("voting is off (config.json): no vote comment")
        return
    if ep.get("celebration"):
        text = "بسبوسة مبسوطة بيكم! 🎉 تحبوا الحكاية الجاية تكون عن إيه؟ قولولنا في الكومنتات!"
    elif vote.get("question"):
        text = (f"{vote['question']} ✍️ اكتبوا اختياركم في الكومنتات: "
                f"{vote.get('option_a', '')} ولا {vote.get('option_b', '')}")
    else:
        text = "تحبوا بسبوسة تعمل إيه في الجزء الجاي؟ قولولنا في الكومنتات!"
    state_path = ROOT / os.environ.get("STORY_STATE", "story_state.json")
    if os.environ.get("PUBLISH_AT") and os.environ.get("UPLOAD_MODE") != "direct" and not ep.get("celebration") and state_path.exists():
        # YouTube refuses comments on a not-yet-public (scheduled) video (403).
        # Park it; pipeline/post_pending.py (comment.yml) posts it right after
        # the video goes public.
        st = json.loads(state_path.read_text())
        st["pending_comment"] = {"video_id": vid, "text": text, "publish_at": os.environ["PUBLISH_AT"]}
        state_path.write_text(json.dumps(st, ensure_ascii=False, indent=2))
        print("channel comment parked until the video is public:", vid)
        return
    try:
        body = json.dumps({"snippet": {"videoId": vid,
            "topLevelComment": {"snippet": {"textOriginal": text}}}}).encode()
        req = urllib.request.Request(
            "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
            data=body, method="POST",
            headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            print("posted channel comment:", json.load(r)["id"])
    except Exception as e:
        print(f"channel comment failed (video is live regardless): {e}")

def add_to_playlist(vid: str, tok: str) -> None:
    """Every episode lands in its storyline's playlist (owner approved, and
    the OAuth token now carries youtube.force-ssl). A new storyline (state.story
    changed) gets a fresh playlist named after the story."""
    state_path = ROOT / os.environ.get("STORY_STATE", "story_state.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    pl = state.get("playlist_id")
    story = state.get("story")
    if not pl and story:
        body = json.dumps({"snippet": {"title": f"حكاية {story} | حكايات بسبوسة | الموسم 1",
                                        "description": f"كل أجزاء حكاية {story} من حكايات بسبوسة"},
                           "status": {"privacyStatus": "public"}}).encode()
        req = urllib.request.Request("https://www.googleapis.com/youtube/v3/playlists?part=snippet,status",
            data=body, method="POST",
            headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            pl = json.load(r)["id"]
        state["playlist_id"] = pl
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        print("created story playlist:", pl)
    if not pl:
        print("no playlist_id/story in state; skipping playlist add")
        return
    body = json.dumps({"snippet": {"playlistId": pl,
        "resourceId": {"kind": "youtube#video", "videoId": vid}}}).encode()
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet",
        data=body, method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    import time
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60):
                print("added to playlist:", pl)
            break
        except Exception as e:
            detail = e.read().decode()[:300] if hasattr(e, "read") else ""
            print(f"playlist add attempt {attempt + 1} failed: {e} {detail}")
            if attempt == 3:
                print("playlist add failed (non-fatal)")
            else:
                time.sleep(20)
                req = urllib.request.Request(req.full_url, data=req.data, method="POST", headers=dict(req.header_items()))
    thumb = ROOT / "thumb.jpg"
    if thumb.exists():
        req = urllib.request.Request(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
            data=thumb.read_bytes(), method="POST",
            headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"})
        with urllib.request.urlopen(req, timeout=120):
            pass
        print("custom thumbnail set")

if __name__ == "__main__":
    sys.exit(main())
