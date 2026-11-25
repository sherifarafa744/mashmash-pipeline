"""Read the audience's vote from the previous episode's comments and record
the winner in the story state BEFORE gen_script writes the next part.

The previous episode asked vote.question with option_a / option_b (recorded in
episode.json and carried in the arc's state file). Here we count matching
comments on that episode's video and write state.vote_result; gen_script then
follows the majority. Any failure is a no-op: the episode must still generate.
Free tier: 2-3 YouTube Data API reads (~3 quota units of the 10k/day default).
"""
import json, os, pathlib, re, sys, urllib.parse, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from upload import access_token  # same OAuth refresh-token flow

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARABIC_DIACRITICS = re.compile(r"[ً-ْٰـ]")


def norm(s: str) -> str:
    s = ARABIC_DIACRITICS.sub("", s or "")
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", s).strip().lower()


def keyword(option_norm: str) -> str:
    words = [w for w in option_norm.split() if len(w) >= 4]
    return max(words, key=len) if words else option_norm


def main() -> None:
    sp = ROOT / os.environ.get("STORY_STATE", "story_state.json")
    if not sp.exists():
        print("no state file; nothing to count")
        return
    st = json.loads(sp.read_text())
    vote, vid = st.get("vote"), st.get("last_video_id")
    if not vote or not vid:
        print("no pending vote or no previous video; skipping")
        return
    try:
        tok = access_token()
        # Our own channel id, so the channel's pinned question comment is
        # never counted as a vote.
        req = urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={vid}",
            headers={"Authorization": f"Bearer {tok}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            own_channel = json.load(r)["items"][0]["snippet"]["channelId"]
        comments, page = [], None
        for _ in range(2):  # up to 200 top-level comments
            qs = {"part": "snippet", "videoId": vid, "maxResults": "100",
                  "order": "relevance", "textFormat": "plainText"}
            if page:
                qs["pageToken"] = page
            req = urllib.request.Request(
                "https://www.googleapis.com/youtube/v3/commentThreads?" + urllib.parse.urlencode(qs),
                headers={"Authorization": f"Bearer {tok}"})
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)
            for item in out.get("items", []):
                sn = item["snippet"]["topLevelComment"]["snippet"]
                if sn.get("authorChannelId", {}).get("value") == own_channel:
                    continue
                comments.append(sn.get("textDisplay", ""))
            page = out.get("nextPageToken")
            if not page:
                break
        a_txt, b_txt = norm(vote["option_a"]), norm(vote["option_b"])
        a_key, b_key = keyword(a_txt), keyword(b_txt)
        ca = cb = 0
        for c in comments:
            n = norm(c)
            hit_a = a_txt in n or (a_key and a_key in n)
            hit_b = b_txt in n or (b_key and b_key in n)
            if hit_a and hit_b:
                continue  # quoting both options (e.g. the question itself)
            if hit_a:
                ca += 1
            elif hit_b:
                cb += 1
        winner = "a" if ca > cb else "b" if cb > ca else ("tie" if ca or cb else "none")
        st["vote_result"] = {"question": vote["question"],
                             "option_a": vote["option_a"], "option_b": vote["option_b"],
                             "votes_a": ca, "votes_b": cb, "winner": winner}
        sp.write_text(json.dumps(st, ensure_ascii=False, indent=2))
        print(f"vote counted on {vid}: {ca} vs {cb} -> {winner}")
    except Exception as e:
        # Never block an episode on comment reading.
        print(f"vote counting skipped ({e}); the model continues without a result")


if __name__ == "__main__":
    sys.exit(main())
