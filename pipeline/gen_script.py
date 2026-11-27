"""Generate the next episode script with the Gemini API (free tier).

Outputs episode.json: {title, hook, scenes: [{narration, image_prompt}], outro}
Story state (story_state.json) carries the cliffhanger into the next episode.
Free tier: Flash ~20 req/day, Flash-Lite ~500 req/day; one call per episode.
"""
import json, os, re, sys, pathlib, time, urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]
MODELS = [os.environ["GEMINI_SCRIPT_MODEL"]] if os.environ.get("GEMINI_SCRIPT_MODEL") else [
    "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
ROOT = pathlib.Path(__file__).resolve().parent.parent
try:
    _CFG = json.loads((ROOT / "config.json").read_text())
except Exception:
    _CFG = {}
VOTE_ON = _CFG.get("vote", True)
DANGER_FIRST = bool(_CFG.get("danger_first"))
LOOP_END = bool(_CFG.get("loop_end"))
HOOK_Q = _CFG.get("hook_mode") == "known_char_question"  # experiment B (from 2026-11-28)

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
sentence <= 14 words.

Rules: VIRAL SHORT FORMAT (mandatory, every episode):
1. OPENING: the FIRST narration sentence is a shock/action line of AT MOST 7 words, in this episode's hook_style - it IS the dangerous moment happening right now ("الثعبان نزل على بسبوسة!"). No greeting, no "كان في مرة", no setting or weather, no introduction. Scene 1 image_prompt shows that dangerous moment itself, mid-motion, never calm scenery. hook_text and that first sentence say the same thing.
2. LENGTH: exactly 5 or 6 scenes, 28-36 seconds when spoken: the WHOLE narration is 50-66 words (the original calm voice speaks ~2 words/second), each narration line one spoken sentence of at most 14 words (the last scene may have up to 3 short sentences). Trim anything that does not move the plot.
3. PAYOFF: around scenes 3-4 give a small payoff the viewer can enjoy: the problem of the opening is solved or a secret is revealed, in one clear beat. Then the NEW twist/cliffhanger starts from it. Every scene still ends on rising tension.
4. LOOP: after naming the next part, the LAST sentence echoes the OPENING IDEA in DIFFERENT words (same danger or image, new phrasing, e.g. opening "الثعبان نزل على بسبوسة!" -> ending "وفين الثعبان ده دلوقتي؟"). NEVER repeat the opening sentence or its key phrase verbatim.
5. ENDING: the last scene gives the cliffhanger matching ending_structure, then the vote question, then closes with "انتظروا الجزء" + the NEXT part's Arabic ordinal (given in the user message), NO day or time reference (never بكرة, النهارده, or any date), then the one-line loop-back echo. Never let the story just stop.
6d. TITLE SEARCH WORDS: the title always names the character (بسبوسة) and the story keyword (for example the lamp, the map, the temple) in natural words people search for, plus the hook, in the style of "بسبوسة لقت خريطة كنز في سوق السمك؟! 😱"; the part number is added after the title automatically. Never a generic or celebration-style title. Only state facts that actually happen in the episode.
6c. TITLE VARIETY: the audience is a general family audience, never framed as "children" (no "للأطفال", no kids framing in title, hook or narration). Vary the title SHAPE every episode; rotate among: a question about the danger ("مين هيلحق بسبوسة؟"), a short statement of the event ("العقرب ظهر فجأة"), a promise ("اللي حصل بعد الصندوق مش هتصدقه" style but without clickbait the episode does not deliver), a quoted line from the narration, a contrast ("بسبوسة ضد العقرب الذهبي"). Do NOT reuse the "X.. مين هيعمل Y؟!" shape if any of the last 3 titles in state.recent_openings used it; vary punctuation and emojis too (not always "؟!" and the same two emojis). Vary the hook too: a different hook_style and a different opening type from the last 3 episodes.
6b. TITLE MATCH: the title must name the main danger or event that actually happens in THIS episode's scenes (use the same key nouns as the narration and cliffhanger, e.g. the creature, object or place shown); never a title about something the episode does not show.
6. NO NEAR-DUPLICATES: the opening line, hook_text, title, and vote question must not repeat or closely paraphrase any previous episode of ANY arc (state.recent_openings lists them); change the verb, the danger and the structure.
Egyptian dialect throughout; image_prompt is an English visual description of the scene (no text in image). Update state for next time, appending this episode's setting, conflict_type, ending_structure, story_type and hook_style to the used lists (keep each to the last 6). Also return "opening_line": the exact first narration sentence, and "beat_scene": the 1-based number of the scene whose first sentence is the shock/twist beat (usually 4 or 5; never 1)."""


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


def words(t: str) -> int:
    return len(re.findall(r"\S+", t))


def first_sentence(t: str) -> str:
    return re.split(r"[.!؟?!…]+", t.strip(), 1)[0].strip()


def est_seconds(ep) -> float:
    return sum(words(sc["narration"]) for sc in ep["scenes"]) / 1.85


def problems(ep, recent) -> list:
    out = []
    sc = ep.get("scenes", [])
    if not 5 <= len(sc) <= 6:
        out.append(f"need exactly 5-6 scenes, got {len(sc)}")
    if sc:
        fs = first_sentence(sc[0]["narration"])
        if words(fs) > 7:
            out.append(f"first sentence has {words(fs)} words, max 7: {fs}")
        if fs in recent:
            out.append("first sentence repeats a previous opening")
    if sc:
        o = first_sentence(sc[0]["narration"])
        last = sc[-1]["narration"]
        if o and o in last:
            out.append("the ending repeats the opening sentence verbatim; echo it in different words")
        if not VOTE_ON and ("اكتبوا" in last or "التعليقات" in last or "الكومنتات" in last):
            out.append("voting is off: remove the vote question and any ask to comment")
    if HOOK_Q and sc:
        fs0 = first_sentence(sc[0]["narration"])
        if "؟" not in fs0 and "?" not in fs0:
            out.append("hook experiment: the first sentence must be a shocking question naming a known character")
    t = ep.get("title", "")
    def shape(x): return (".." in x, "؟" in x, "!" in x)
    try:
        prev = [json.loads(l).get("title", "") for l in (ROOT / "episode_log.jsonl").read_text().splitlines()[-4:]]
    except Exception:
        prev = []
    if t and sum(1 for x in prev if shape(x) == shape(t)) >= 2:
        out.append("title shape (dots/question/exclamation pattern) repeats 2+ of the last 4 titles; use a different title shape")
    if any(w in t for w in ("للأطفال", "اطفال", "أطفال")):
        out.append("do not frame the title for children; use a general family audience")
    total = sum(words(x["narration"]) for x in sc)
    if not 48 <= total <= 68:
        out.append(f"narration is {total} words, need 48-68")
    return out


def trim_scenes(ep) -> None:
    """Last resort: drop middle scenes (keep opening, payoff region, ending)."""
    sc = ep["scenes"]
    while len(sc) > 5 and est_seconds(ep) > 36:
        del sc[len(sc) // 2 - 1]
    ep["scenes"] = sc


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
                if ep and re.search(r"[\u0400-\u04FF\u0370-\u03FF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF]", json.dumps(ep, ensure_ascii=False)):
                    print(f"{model} attempt {attempt + 1}: reply has non-Arabic/Latin letters (glitch), retrying")
                    continue
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
    recent = []
    for f in sorted(ROOT.glob("episodes/*/ep*.json")):
        try:
            e = json.loads(f.read_text())
            recent.append(e.get("opening_line") or first_sentence(e["scenes"][0]["narration"]))
            recent.append(e.get("title", ""))
        except Exception:
            pass
    recent = [r for r in recent if r][-24:]
    user += "\nstate.recent_openings (all arcs, do not repeat or paraphrase): " + json.dumps(recent, ensure_ascii=False)
    if not VOTE_ON:
        user += ("\nVOTING IS OFF for this test: do NOT include any vote question, any options, any line asking viewers to answer or comment, "
                 "and return NO vote object. Ignore every vote instruction above and state.vote_result. The last scene is: cliffhanger, then the next-part naming, then the different-words echo of the opening.")
    if DANGER_FIRST:
        user += ("\nSCENE 1 DANGER RULE: the danger/creature named in the first narration sentence and hook_text (for example the golden scorpion) "
                 "MUST be clearly visible, large and central, in the scene 1 image_prompt from the very first frame, with Basbusa (the small orange cat with the blue scarf) in the same frame as the main character. "
                 "No calm shot, no close-up of another character alone, no setting-only shot in scene 1.")
    if LOOP_END:
        user += ("\nLOOP RULE: the LAST scene image_prompt must reuse the SAME location, camera framing, lighting and Basbusa pose/position as the scene 1 image_prompt, "
                 "so the final frame looks almost like the first frame; the only change is a new hint of the cliffhanger (a shadow, an eye, a glow) in the background. "
                 "The last narration still ends with the cliffhanger and \"انتظروا الجزء\" + the next ordinal.")
    if HOOK_Q:
        user += ("\nHOOK EXPERIMENT (overrides the hook-variety rules above for the hook only): the FIRST narration sentence MUST be a shocking QUESTION of at most 7 words, "
                 "hook_style shocking_question, that names a KNOWN recurring character (بسبوسة or the companion in state.companion) and asks about something strange or dangerous happening to them right now, "
                 "in the style of: \"ليه بندق طار في الهواء فجأة؟\". hook_text says the same question. Keep the title variety rule.")
    user += f"\nThis is part {part}. The closing line MUST name the next part: \"انتظروا الجزء {nxt}!\""
    body = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }).encode()
    import retry

    def one_pass() -> str:
        last = None
        for model in MODELS:
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}",
                    data=body, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    out = json.load(r)
                print("script model:", model)
                return out["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:  # 503 high demand, 429 quota, etc.
                last = e
                print(f"{model} failed: {e}", flush=True)
                time.sleep(15)
        raise RuntimeError(f"all Gemini script models failed: {last}")

    used_model = None
    try:
        # Retry Gemini over a long window; leave ~25 min for voice, images, assembly.
        text = retry.call(one_pass, "script", reserve_s=1500, cap_s=10800, spacing_s=240)
    except SystemExit:
        if os.environ.get("ALLOW_WEAK_FALLBACK") != "1":
            raise
        print("ALLOW_WEAK_FALLBACK=1: trying Cloudflare Workers AI")
        text = cloudflare_script(SYSTEM, user)
        used_model = CF_MODELS[0] if text else None
        if not text:
            raise
    episode = json.loads(text)
    # Enforce the viral format: ask Gemini again with the exact problems (up to 3x).
    for fix in range(3):
        issues = problems(episode, recent)
        if not issues:
            break
        print("format issues, regenerating:", issues, flush=True)
        body = json.dumps({
            "system_instruction": {"parts": [{"text": SYSTEM}]},
            "contents": [{"role": "user", "parts": [{"text": user + "\nYour previous draft broke the format: " + "; ".join(issues) + ". Rewrite the whole episode fixing exactly this."}]}],
            "generationConfig": {"response_mime_type": "application/json"}}).encode()
        try:
            episode = json.loads(retry.call(one_pass, "script-fix", reserve_s=1500, cap_s=1200, spacing_s=120))
        except SystemExit:
            break
    if est_seconds(episode) > 36 or len(episode["scenes"]) > 6:
        trim_scenes(episode)
        print("trimmed scenes to fit 28-36s")
    episode["format_issues"] = problems(episode, recent)
    episode["opening_line"] = first_sentence(episode["scenes"][0]["narration"])
    if used_model:
        episode["script_model"] = "cloudflare:" + used_model
    if _CFG.get("build_tag"): episode["build_tag"] = _CFG["build_tag"]
    if DANGER_FIRST: episode["danger_first"] = True
    if LOOP_END: episode["loop_end"] = True
    episode["hook_mode"] = "known_char_question" if HOOK_Q else "default"
    episode["part"] = part  # story_type comes straight from the model output
    (ROOT / "episode.json").write_text(json.dumps(episode, ensure_ascii=False, indent=2))
    new_state = {"episode": part, "next": episode["cliffhanger"], **episode.get("state", {})}
    # The result of the PREVIOUS vote is consumed by this episode; drop it.
    # This episode's own vote question is carried forward for vote.py to count.
    new_state.pop("vote_result", None)
    if VOTE_ON and episode.get("vote"):
        new_state["vote"] = episode["vote"]
    if not VOTE_ON:
        new_state.pop("vote", None)
        episode.pop("vote", None)
        (ROOT / "episode.json").write_text(json.dumps(episode, ensure_ascii=False, indent=2))
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
