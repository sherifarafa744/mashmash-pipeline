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
{"title": "...", "hook_text": "...", "hook_style": "...", "scenes": [{"narration": "...", "image_prompt": "..."}, ...],
 "vote": {"question": "...", "option_a": "...", "option_b": "..."},
 "cliffhanger": "...", "story_type": "...", "state": {"location": "...", "goal": "...", "danger": "...", "story": "...",
 "setting": "...", "conflict_type": "...", "ending_structure": "...",
 "companion": {"name": "...", "role": "...", "description": "..."},
 "used": {"settings": [...], "conflicts": [...], "endings": [...], "types": [...], "hook_styles": [...]}}}
state.story: short Arabic name of the current storyline (e.g. "كنز جزيرة التونة
الذهبية"); keep the SAME name across the whole arc, change it only when the
arc fully ends and a new story begins.
hook_text: 3-7 words of Egyptian Arabic on-screen text shown big for the first 2.6
seconds, stating the episode's conflict or question (e.g. "بسبوسة في ورطة كبيرة!").
No emojis, no punctuation overload - it must read in one glance.
hook_style: viewers decide in the first 3 seconds, so we rotate opening-hook
styles and track which one retains best. Pick a NEW style not in
used.hook_styles: shocking_question (سؤال صادم), danger_warning (تحذير من خطر
قريب), surprising_fact (معلومة مفاجئة), challenge (تحدي أو رهان), mystery (لغز
غامض), cry_for_help (صرخة استغاثة). Write the chosen English snake_case name in
hook_style, and make BOTH hook_text and the first narration sentence deliver it.

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
AUDIENCE VOTE: if state.vote_result.winner is "a" or "b", the audience has
chosen what happens next - this episode's plot MUST follow that option
(state.vote_result.option_a / option_b). If it is "tie" or "none", choose what
fits the story best.
COMPANION: every arc has exactly ONE recurring secondary character (a friend
or a rival) recorded in state.companion: a fixed Egyptian name, role
("friend"/"rival"), and a short fixed English visual description. Invent it at
arc start and keep it IDENTICAL across the whole arc (name, role, description
never change mid-arc; a new arc gets a new companion). The companion appears
or is mentioned in every episode and matters to the plot; when it appears in a
scene, embed companion.description verbatim in that scene's image_prompt.
VOTE QUESTION: near the end, after the cliffhanger and before naming the next
part, Basbusa asks viewers a simple either-or question about what she should do
next. vote.question is short Egyptian Arabic; vote.option_a and vote.option_b
are two SHORT, clearly different choices (<= 5 words each, easy to type in a
comment). The last scene's narration speaks the vote question and both options
and tells viewers to answer in the comments, then closes with "انتظروا الجزء"
+ the next part's ordinal as usual. The last scene narration may be up to 3
short sentences (cliffhanger + vote + part naming); all other lines stay one
sentence <= 18 words.

Rules: RETENTION IS EVERYTHING - viewers leave in the first 3 seconds, so the opening decides everything. The FIRST narration sentence is the hook itself: <= 12 words, it IS the conflict, question or danger in this episode's hook_style - no greeting, no "كان في مرة", no setting or weather description, no character introduction. Scene 1 narration must open mid-action with the conflict or question in the first 1-2 seconds (a surprising fact or question) that makes skipping feel like missing out - never a slow intro. Scene 1 image_prompt must show the conflict moment itself, action mid-motion - never calm establishing scenery. Every scene must end on rising tension or an open question so the viewer stays to the end. 6-8 scenes (target ~55-65 seconds total, the hit length in this niche); each narration line is one spoken sentence, Egyptian
dialect, <= 18 words; image_prompt is an English visual description of the
scene (no text in image). The LAST scene narration must close with a spoken cliffhanger hook in Egyptian Arabic matching this episode's ending_structure, e.g. asking what happens next and saying "انتظروا الجزء" + the NEXT part's Arabic ordinal (given in the user message) with NO day or time reference (never say بكرة, النهارده, or any date - episodes come out twice a day) - never let the story just stop; update state for next time, appending this episode's setting, conflict_type, ending_structure, story_type and hook_style to the used lists (keep each to the last 6)."""


GEMINI_BUDGET_S = int(os.environ.get("GEMINI_BUDGET_S", "300"))  # then fall back
CF_MODELS = ["@cf/meta/llama-3.3-70b-instruct-fp8-fast", "@cf/meta/llama-3.1-70b-instruct"]


def _extract_json(txt: str):
    """First balanced JSON object in a model reply (may be fenced)."""
    i = txt.find("{")
    if i < 0:
        return None
    depth, in_str, esc = 0, False, False
    for j in range(i, len(txt)):
        c = txt[j]
        if in_str:
            esc = (c == "\\" and not esc)
            if c == '"' and not esc:
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return txt[i:j + 1]
    return None


def cloudflare_script(system: str, user: str):
    """Free Workers AI text model, used only when every Gemini model failed.
    Returns episode JSON text or None. Validates the keys the pipeline needs."""
    acct, tok = os.environ.get("CF_ACCOUNT_ID"), os.environ.get("CF_API_TOKEN")
    if not (acct and tok):
        return None
    for model in CF_MODELS:
        for attempt in range(2):
            try:
                body = json.dumps({"messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user + "\nWrite ALL Arabic in Egyptian colloquial dialect (عامية مصرية: مثل \"عملت\"، \"هتعمل إيه\"، \"فين\")، never Modern Standard (no \"ماذا\" / \"هل\"). Keep every rule above. Return ONLY the JSON object, no other text."}],
                    "max_tokens": 4096, "temperature": 0.8}).encode()
                req = urllib.request.Request(
                    f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}",
                    data=body, headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    out = json.load(r)
                resp = out["result"]["response"]
                txt = json.dumps(resp, ensure_ascii=False) if isinstance(resp, dict) else _extract_json(resp or "")
                ep = json.loads(txt) if txt else None
                if (ep and ep.get("title") and ep.get("cliffhanger")
                        and 4 <= len(ep.get("scenes", [])) <= 12
                        and all(sc.get("narration") and sc.get("image_prompt") for sc in ep["scenes"])):
                    print("script model (fallback):", model)
                    return json.dumps(ep, ensure_ascii=False)
                print(f"{model} attempt {attempt + 1}: reply missing required fields")
            except Exception as e:
                print(f"{model} attempt {attempt + 1} failed: {e}")
                time.sleep(5)
    return None


def main() -> None:
    state_path = ROOT / os.environ.get("STORY_STATE", "story_state.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else None
    ords = ["التاني","التالت","الرابع","الخامس","السادس","السابع","التامن","التاسع","العاشر",
            "الحادي عشر","التاني عشر","التالت عشر","الرابع عشر","الخامس عشر"]
    part = (state or {}).get("episode", 0) + 1
    nxt = ords[part - 1] if part - 1 < len(ords) else str(part + 1)
    if state:
        user = "Continue the story. Current state: " + json.dumps(state, ensure_ascii=False)
    elif os.environ.get("ARC_DIR") == "arc2":
        user = ("Write episode 1 of a NEW, different storyline (not a treasure map): "
                "Basbusa finds a mysterious old brass lamp in her grandmother's attic in old Cairo. "
                "Start a fresh serialized arc.")
    user += f"\nThis is part {part}. The closing line MUST name the next part: \"انتظروا الجزء {nxt}!\""
    body = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }).encode()
    text = None
    last_err = None
    t0 = time.time()
    for model in MODELS:
        if time.time() - t0 > GEMINI_BUDGET_S:
            break
        for attempt in range(3):
            if time.time() - t0 > GEMINI_BUDGET_S:
                break
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
    used_model = None
    if not text:
        print(f"Gemini failed ({last_err}); trying Cloudflare Workers AI fallback")
        text = cloudflare_script(SYSTEM, user)
        used_model = CF_MODELS[0] if text else None
    if not text:
        raise RuntimeError(f"all script models failed: {last_err}")
    episode = json.loads(text)
    if used_model:
        episode["script_model"] = "cloudflare:" + used_model
    episode["part"] = part  # story_type comes straight from the model output
    (ROOT / "episode.json").write_text(json.dumps(episode, ensure_ascii=False, indent=2))
    new_state = {"episode": part, "next": episode["cliffhanger"], **episode.get("state", {})}
    # The result of the PREVIOUS vote is consumed by this episode; drop it.
    # This episode's own vote question is carried forward for vote.py to count.
    new_state.pop("vote_result", None)
    if episode.get("vote"):
        new_state["vote"] = episode["vote"]
    # The storyline name persists across an arc; the model only changes it when
    # a new arc begins. playlist_id always carries over (upload.py owns it).
    if state:
        if "story" not in new_state and state.get("story"):
            new_state["story"] = state["story"]
        # The companion survives the whole arc even if the model omits it once.
        if "companion" not in new_state and state.get("companion"):
            new_state["companion"] = state["companion"]
        if state.get("playlist_id"):
            new_state["playlist_id"] = state["playlist_id"]
    state_path.write_text(json.dumps(new_state, ensure_ascii=False, indent=2))
    print("episode:", part, episode["title"], "-", len(episode["scenes"]), "scenes")


if __name__ == "__main__":
    sys.exit(main())
