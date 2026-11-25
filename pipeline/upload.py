"""Upload to YouTube with the Data API resumable protocol + OAuth refresh token.

PUBLIC uploads approved by the channel owner (WhatsApp 2026-11-25).

videos.insert has its own bucket: 100 uploads/day/project (post-Jun-2026).
OAuth consent screen must be 'In production' or refresh tokens die in 7 days.
Uploads as PRIVATE; publishing is a human decision.
"""
import json, os, pathlib, sys, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent

def access_token() -> str:
    body = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request(
            "https://oauth2.googleapis.com/token", data=body), timeout=60) as r:
        return json.load(r)["access_token"]

def main() -> None:
    ep = json.loads((ROOT / "episode.json").read_text())
    video = (ROOT / "episode_final.mp4").read_bytes()
    if ep.get("celebration"):
        # Milestone Short: no part number, no cliffhanger, no story playlist.
        title = f"{ep['title']} | بسبوسة"
        desc = "بسبوسة بتحتفل معاكم وتشكركم على حبكم! 🎉\n"
    else:
        title = f"{ep['title']} | الجزء {ep.get('part', 1)} | بسبوسة"
        desc = f"الجزء {ep.get('part', 1)} من حكايات بسبوسة\n" + ep.get("cliffhanger", "") + "\n"
    meta = json.dumps({"snippet": {
            "title": title,
            "description": desc + "\nالموسيقى: Sneaky Snitch - Kevin MacLeod (incompetech.com)\nLicensed under Creative Commons: By Attribution 4.0\nhttps://creativecommons.org/licenses/by/4.0/\n#بسبوسة #قصص_قطط #شورتس #قصص_حيوانات",
            "categoryId": "24", "tags": ["بسبوسة","قصص قطط","حكايات بسبوسة","قطط","قصص اطفال","شورتس","Shorts","قصص مصورة"]},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}).encode()
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

def add_to_playlist(vid: str, tok: str) -> None:
    """Every episode lands in its storyline's playlist (owner approved, and
    the OAuth token now carries youtube.force-ssl). A new storyline (state.story
    changed) gets a fresh playlist named after the story."""
    state_path = ROOT / os.environ.get("STORY_STATE", "story_state.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    pl = state.get("playlist_id")
    story = state.get("story")
    if not pl and story:
        body = json.dumps({"snippet": {"title": f"بسبوسة و{story} 🗺️ | الموسم 1",
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
    try:
        with urllib.request.urlopen(req, timeout=60):
            print("added to playlist:", pl)
    except Exception as e:
        # Never fail the episode over a playlist add; the reviewer can add it manually.
        print("playlist add failed (non-fatal):", e)
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
