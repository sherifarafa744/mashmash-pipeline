"""Post parked channel comments once their video is public.

upload.py parks the vote comment in state.pending_comment for scheduled
videos (YouTube refuses comments on a not-yet-public video). This runs just
after each slot (comment.yml) and posts the comment when videos.list says the
video is public, then clears the park. Idempotent.
"""
import json, pathlib, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from upload import access_token

ROOT = pathlib.Path(__file__).resolve().parent.parent


def save(path, st):
    path.write_text(json.dumps(st, ensure_ascii=False, indent=2))


def main() -> None:
    changed = False
    tok = None
    for path in sorted(ROOT.glob("story_state*.json")):
        st = json.loads(path.read_text())
        pc = st.get("pending_comment")
        if not pc:
            continue
        tok = tok or access_token()
        hdr = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
        req = urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/videos?part=status&id={pc['video_id']}", headers=hdr)
        items = json.load(urllib.request.urlopen(req, timeout=60)).get("items", [])
        privacy = items[0]["status"]["privacyStatus"] if items else "missing"
        print(path.name, pc["video_id"], "privacy:", privacy)
        if privacy == "public":
            body = json.dumps({"snippet": {"videoId": pc["video_id"],
                "topLevelComment": {"snippet": {"textOriginal": pc["text"]}}}}).encode()
            try:
                req = urllib.request.Request(
                    "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
                    data=body, method="POST", headers=hdr)
                print("posted channel comment:", json.load(urllib.request.urlopen(req, timeout=60))["id"])
            except Exception as e:
                print("comment failed:", e)
            st.pop("pending_comment")
            save(path, st)
            changed = True
        elif privacy == "missing":
            st.pop("pending_comment")
            save(path, st)
            changed = True
    print("changed" if changed else "nothing to do")


if __name__ == "__main__":
    main()
