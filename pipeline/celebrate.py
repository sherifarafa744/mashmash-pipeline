"""Milestone celebration Short (~20-30s): Basbusa celebrates and thanks the
viewers. NOT a story episode: no cliffhanger, no part number, arc state
untouched.

Trigger: the review agent commits milestone.json {"pending": true, "kind":
"subscribers"|"views", "value": <verified number>} when Studio crosses a
milestone (subs 10/50/100/500/1000, total views 10K/100K). The next daily slot
runs this instead of a story episode, then clears the flag in its archive
commit.

Numbers: the narration NEVER states an exact subscriber/view count, so the
Short stays true whenever it publishes (only the review agent sees the number).
Free tier: 1 Gemini script call + 1 TTS call + 3 FLUX images (replaces, not
adds to, the slot's normal usage).
"""
import json, os, pathlib, subprocess, sys, time, urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]
MODELS = [os.environ["GEMINI_SCRIPT_MODEL"]] if os.environ.get("GEMINI_SCRIPT_MODEL") else [
    "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
ROOT = pathlib.Path(__file__).resolve().parent.parent

SYSTEM = """You write Egyptian-Arabic narration for a very short vertical YouTube
celebration Short about Basbusa (بسبوسة), a female cartoon cat with a blue
scarf (feminine Egyptian Arabic grammar; never any other name). This is NOT a
story episode: Basbusa celebrates a channel milestone and thanks the viewers
with joy and warmth.
Return STRICT JSON only:
{"title": "...", "hook_text": "...", "hook_style": "celebration",
 "scenes": [{"narration": "...", "image_prompt": "..."}, ...],
 "cliffhanger": "", "story_type": "celebration"}
Rules: EXACTLY 3 scenes; the whole Short is 20-30 seconds. Each narration line
is one spoken sentence, Egyptian dialect, <= 15 words. Scene 1 opens
mid-celebration with the hook in the first second - no slow intro. Basbusa
dances, celebrates, thanks the viewers for their love and asks them to keep
watching and subscribe. NEVER state or hint an exact subscriber or view number.
No cliffhanger, no "انتظروا الجزء", no story plot. Title: joyful celebration
with 1-2 emojis, under 70 characters. hook_text: 3-6 Egyptian Arabic words for
the first 2.6 seconds, no emojis, reads in one glance. image_prompt: English
visual description (no text in image): Basbusa dancing, confetti, balloons,
party lights, fireworks over Cairo at night."""


def main() -> None:
    flag = json.loads((ROOT / "milestone.json").read_text())
    kind = flag.get("kind", "milestone")
    user = ("Write the celebration Short now. The milestone category is: " + kind +
            ". Remember: no exact numbers anywhere.")
    body = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }).encode()
    text, last_err = None, None
    for model in MODELS:
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}",
                    data=body, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    out = json.load(r)
                text = out["candidates"][0]["content"]["parts"][0]["text"]
                print("script model:", model)
                break
            except Exception as e:
                last_err = e
                print(f"{model} attempt {attempt + 1} failed: {e}")
                time.sleep(20 * (attempt + 1))
        if text:
            break
    if not text:
        raise RuntimeError(f"all script models failed: {last_err}")
    episode = json.loads(text)
    episode["celebration"] = True
    episode["scenes"] = episode["scenes"][:3]  # hard cap: 20-30s, never longer
    (ROOT / "episode.json").write_text(json.dumps(episode, ensure_ascii=False, indent=2))
    print("celebration:", episode["title"], "-", len(episode["scenes"]), "scenes")
    here = pathlib.Path(__file__).parent
    for step in ["gen_voice.py", "gen_images.py", "assemble.py", "gen_thumbnail.py", "upload.py"]:
        print("==", step, flush=True)
        subprocess.run([sys.executable, str(here / step)], check=True)


if __name__ == "__main__":
    sys.exit(main())
