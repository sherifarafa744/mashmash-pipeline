"""Generate the next episode script with the Gemini API (free tier).

Outputs episode.json: {title, hook, scenes: [{narration, image_prompt}], outro}
Story state (story_state.json) carries the cliffhanger into the next episode.
Free tier: Flash ~20 req/day, Flash-Lite ~500 req/day; one call per episode.
"""
import json, os, sys, pathlib, time, urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]
MODELS = [os.environ["GEMINI_SCRIPT_MODEL"]] if os.environ.get("GEMINI_SCRIPT_MODEL") else [
    "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
ROOT = pathlib.Path(__file__).resolve().parent.parent

SYSTEM = """You write Egyptian-Arabic narration for a vertical YouTube Shorts
series about Basbusa (بسبوسة), a female cartoon cat with a blue scarf, in serialized cliffhanger parts. The character is ALWAYS called بسبوسة in the narration and titles (feminine Egyptian Arabic grammar). Never call her مشمش or any other name.
Return STRICT JSON only. The title must follow the proven Arabic AI-story format: a conflict or question with 1-2 emojis that makes skipping feel like losing something, e.g. "بسبوسة ضد القط الأعور.. مين هياخد الكنز؟! 😱" - under 70 characters, no clickbait the episode does not deliver.
{"title": "...", "hook_text": "...", "scenes": [{"narration": "...", "image_prompt": "..."}, ...],
 "cliffhanger": "...", "story_type": "...", "state": {"location": "...", "goal": "...", "danger": "...", "story": "...",
 "setting": "...", "conflict_type": "...", "ending_structure": "...",
 "used": {"settings": [...], "conflicts": [...], "endings": [...], "types": [...]}}}
state.story: short Arabic name of the current storyline (e.g. "كنز جزيرة التونة
الذهبية"); keep the SAME name across the whole arc, change it only when the
arc fully ends and a new story begins.
hook_text: 3-7 words of Egyptian Arabic on-screen text shown big for the first 2
seconds, stating the episode's conflict or question (e.g. "بسبوسة في ورطة كبيرة!").
No emojis, no punctuation overload - it must read in one glance.

VARIETY IS MANDATORY - YouTube penalizes mass-produced repetitive content, and
the audience gets bored. Each episode MUST differ from the entries in
state.used (the rolling lists of recent settings, conflicts, endings - keep
each list to the last 6):
- setting: pick a NEW place not in used.settings (e.g. fish market, Nile boat,
  desert ruin, old Cairo alley, rooftop, train, village, school, pharaoh's tomb,
  night carnival, barbershop, metro). Write the chosen one in state.setting.
- conflict_type: pick a NEW type not in used.conflicts (rival, mystery, chase,
  bargain, rescue, secret, bet, misunderstanding, theft, friendship test).
- story_type: pick a NEW type not in used.types. The proven-hit types for this
  niche: action-chase (مطاردة), superpower (قوة خارقة سحرية), rival-conflict
  (صراع مع خصم), kind-moral (موقف طيب وعبرة), mystery (لغز), comedy (كوميديا).
  Rotate through them so we learn what our audience loves most.
- ending_structure: pick a NEW structure not in used.endings (question
  cliffhanger, twist reveal, new character appears, danger revealed, choice
  forced, secret overheard).
CONTINUING PLOT: the story is serialized - scene 1 must resolve or advance the
previous cliffhanger (state.next) within the first scene or two, then escalate
into this episode's new conflict. Never restart, retcon, or repeat a beat.

Rules: RETENTION IS EVERYTHING - the channel has zero subscribers, so every second must earn the next. Scene 1 narration must open mid-action with the conflict or question in the first 1-2 seconds (a surprising fact or question) that makes skipping feel like missing out - never a slow intro. Every scene must end on rising tension or an open question so the viewer stays to the end. 6-8 scenes (target ~55-65 seconds total, the hit length in this niche); each narration line is one spoken sentence, Egyptian
dialect, <= 18 words; image_prompt is an English visual description of the
scene (no text in image). The LAST scene narration must close with a spoken cliffhanger hook in Egyptian Arabic matching this episode's ending_structure, e.g. asking what happens next and saying "انتظروا الجزء" + the NEXT part's Arabic ordinal (given in the user message) with NO day or time reference (never say بكرة, النهارده, or any date - episodes come out twice a day) - never let the story just stop; update state for next time, appending this episode's setting, conflict_type, ending_structure and story_type to the used lists."""


def main() -> None:
    state_path = ROOT / "story_state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else None
    ords = ["التاني","التالت","الرابع","الخامس","السادس","السابع","التامن","التاسع","العاشر",
            "الحادي عشر","التاني عشر","التالت عشر","الرابع عشر","الخامس عشر"]
    part = (state or {}).get("episode", 0) + 1
    nxt = ords[part - 1] if part - 1 < len(ords) else str(part + 1)
    user = ("Continue the story. Current state: " + json.dumps(state, ensure_ascii=False)) if state else "Write episode 1: Basbusa finds a treasure map in the fish market."
    user += f"\nThis is part {part}. The closing line MUST name the next part: \"انتظروا الجزء {nxt}!\""
    body = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }).encode()
    text = None
    last_err = None
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
            except Exception as e:  # 503 high demand, 429 quota, etc.
                last_err = e
                print(f"{model} attempt {attempt + 1} failed: {e}")
                time.sleep(20 * (attempt + 1))
        if text:
            break
    if not text:
        raise RuntimeError(f"all script models failed: {last_err}")
    episode = json.loads(text)
    episode["part"] = part  # story_type comes straight from the model output
    (ROOT / "episode.json").write_text(json.dumps(episode, ensure_ascii=False, indent=2))
    new_state = {"episode": part, "next": episode["cliffhanger"], **episode.get("state", {})}
    # The storyline name persists across an arc; the model only changes it when
    # a new arc begins. playlist_id always carries over (upload.py owns it).
    if state:
        if "story" not in new_state and state.get("story"):
            new_state["story"] = state["story"]
        if state.get("playlist_id"):
            new_state["playlist_id"] = state["playlist_id"]
    state_path.write_text(json.dumps(new_state, ensure_ascii=False, indent=2))
    print("episode:", part, episode["title"], "-", len(episode["scenes"]), "scenes")


if __name__ == "__main__":
    sys.exit(main())
