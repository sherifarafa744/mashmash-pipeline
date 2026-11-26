"""Weekly long-form compilation (8+ min horizontal video).

Retells the week's Shorts arc as ONE cohesive story with new connective
narration, chapter transitions, intro and outro - a genuinely distinct video,
not a concatenation of the Shorts. Public weekly upload approved by the
channel owner (WhatsApp 2026-11-25, "ماشي اعمل اللي شايفه صح").

Steps: script (Gemini) -> voice (Gemini TTS, chunked) -> images (CF flux)
-> assemble (ffmpeg Ken Burns 1920x1080, blurred-pad) -> upload (Data API).

Free-tier budgets (weekly run shares the day with 2 daily runs):
- Gemini TTS: 10 req/day per model -> <=4 chunked calls here, 20s apart (3 RPM).
- CF flux: ~55 images/day; <=24 here + ~14 from the two daily runs.
- YouTube videos.insert: 100/day/project.
"""
import base64, json, os, pathlib, subprocess, sys, time, urllib.parse, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from character import image_prompt
import music as music_lib

ROOT = pathlib.Path(__file__).resolve().parent.parent
API_KEY = os.environ["GEMINI_API_KEY"]
SCRIPT_MODEL = os.environ.get("GEMINI_SCRIPT_MODEL", "gemini-3.8-flash")
TTS_MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
TTS_VOICE = os.environ.get("GEMINI_TTS_VOICE", "Charon")
FONTDIR = "/usr/share/fonts/truetype/noto"
STYLE = ("Noto Naskh Arabic,44,&H00FFFFFF,&H000000FF,&H00141414,&H96000000,"
         "0,0,0,0,100,100,0,0,1,3,1,2,60,60,60,1")
MUSIC_ATTR = ""  # set per build from the picked track (see main)

SYSTEM = """You write Egyptian-Arabic narration for a LONG-FORM (8-10 minute)
horizontal YouTube video retelling one week of the Basbusa (بسبوسة) Shorts
series (a female cartoon cat with a blue scarf) as ONE continuous story.
Always بسبوسة, feminine grammar, never مشمش.
Input: the week's episode JSONs (Shorts parts). Output STRICT JSON:
{"title": "...", "thumb_text": "...", "scenes": [{"narration": "...", "image_prompt": "..."}, ...],
 "cliffhanger": "..."}
This must NOT reuse the Shorts' lines. Rewrite the arc as a cohesive tale:
- scene 1: a cinematic intro hook that states the big question of the whole story.
- Then retell the events in order with NEW wording, adding connective
  narration between the old parts (chapter transitions, motivations,
  reactions) so it flows as one story, not episodes glued together.
- Final scene: an outro inviting viewers to subscribe for next week's part,
  with NO day/time references.
20-24 scenes. Each narration is 2-3 spoken Egyptian-dialect sentences,
35-50 words (target 950-1150 words total => ~8-10 min spoken). image_prompt
is an English visual description (no text in image).
The title: one gripping Arabic line, max 60 characters, 1-2 emojis, no "الجزء"
numbering. It must open a curiosity gap: a specific stake, danger or question
from the story (e.g. who/what/why), never a summary, never the resolution,
never generic words like "حكاية" alone. Also output "thumb_text": 2-4 Arabic
words (no emoji) that will be burned huge on the thumbnail - a punchy question
or danger phrase, different wording from the title.
ENDING: the last 2 scenes must be a CLEAR cliffhanger: the second-to-last scene
ends on a sharp open question or a new danger appearing (concrete, in-story),
the final scene says in one sentence what Basbusa must face next, then a short
invitation to subscribe and comment what she should do. No day/time references.
The JSON also has "cliffhanger": that same open question in one sentence."""


def gemini_text(system: str, user: str) -> dict:
    body = json.dumps({
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{SCRIPT_MODEL}:generateContent?key={API_KEY}",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.load(r)
    return json.loads(out["candidates"][0]["content"]["parts"][0]["text"])


def tts(text: str) -> bytes:
    body = json.dumps({
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": TTS_VOICE}}},
        },
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{TTS_MODEL}:generateContent?key={API_KEY}",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        out = json.load(r)
    return base64.b64decode(out["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])


def cf_image(prompt: str) -> bytes:
    body = json.dumps({"prompt": image_prompt(prompt), "steps": 4}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CF_ACCOUNT_ID']}/ai/run/@cf/black-forest-labs/flux-1-schnell",
        data=body, headers={"Authorization": f"Bearer {os.environ['CF_API_TOKEN']}",
                            "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.load(r)
    return base64.b64decode(out["result"]["image"])


def ts(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def make_thumb(ep: dict, arc: str) -> None:
    """1280x720: first scene image, huge yellow Arabic hook text (libass shapes
    Arabic; emoji stripped, they render as boxes)."""
    import re
    text = re.sub(r"[^0-9A-Za-z\u0600-\u06FF\s?!.\-]", "", ep.get("thumb_text") or ep["title"]).strip()
    (ROOT / "weekly_thumb.ass").write_text("\n".join([
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Noto Naskh Arabic,120,&H0000F0FF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,9,2,2,50,50,50,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{text}"]))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", "1",
        "-i", str(ROOT / "weekly_scenes" / "w1.png"), "-vf",
        "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
        f"eq=contrast=1.15:saturation=1.25,subtitles=weekly_thumb.ass:fontsdir={FONTDIR}",
        "-frames:v", "1", "-q:v", "3", str(ROOT / "weekly_thumb.jpg")], cwd=ROOT, check=True)


def main() -> None:
    # 1. Which episodes are new since the last compilation?
    wstate = json.loads((ROOT / "weekly_state.json").read_text()) if (ROOT / "weekly_state.json").exists() else {}
    arc_dir = ROOT / "episodes" / os.environ.get("ARC_DIR", "arc1")
    done_upto = wstate.get("compiled_upto_" + arc_dir.name, 0)
    eps = sorted(arc_dir.glob("ep*.json"),
                 key=lambda p: json.loads(p.read_text()).get("part", 0))
    eps = [json.loads(p.read_text()) for p in eps]
    new = [e for e in eps if e.get("part", 0) > done_upto]
    if len(new) < 4:
        print(f"only {len(new)} new episodes (need >=4 for a worthwhile compilation); skipping")
        return
    parts = [e["part"] for e in new]
    print("compiling parts:", parts)

    # 2. Long-form script.
    digest = [{"part": e["part"], "title": e["title"],
               "scenes": [s["narration"] for s in e["scenes"]],
               "cliffhanger": e.get("cliffhanger", "")} for e in new]
    ep = gemini_text(SYSTEM, "This week's episodes:\n" + json.dumps(digest, ensure_ascii=False))
    n = len(ep["scenes"])
    (ROOT / "weekly_episode.json").write_text(json.dumps(ep, ensure_ascii=False, indent=2))
    print("long-form script:", n, "scenes -", ep["title"])

    # 3. Voice: chunked TTS (<=4 calls), concat PCM.
    lines = [s["narration"] for s in ep["scenes"]]
    chunk = (len(lines) + 3) // 4
    pcm = b""
    for i in range(0, len(lines), chunk):
        pcm += tts("اقرأ كحكوتي بحماس، وقفة واضحة بين كل جملة:\n" + "\n".join(lines[i:i + chunk]))
        time.sleep(20)
    (ROOT / "weekly_voice.pcm").write_bytes(pcm)
    subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                    "-i", "weekly_voice.pcm", "weekly_voice.wav"], cwd=ROOT, check=True)
    subprocess.run(["ffmpeg", "-y", "-i", "weekly_voice.wav", "-af",
                    "silenceremove=stop_periods=-1:stop_duration=0.45:stop_threshold=-38dB",
                    "weekly_voice_clean.wav"], cwd=ROOT, check=True)
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                  "-of", "csv=p=0", "weekly_voice_clean.wav"],
                                 cwd=ROOT, capture_output=True, text=True).stdout.strip())
    seg, fade = max(total / n + 0.4, 4.0), 0.4
    print(f"voice {total:.1f}s over {n} scenes -> {seg:.2f}s/scene")

    # 4. Images.
    (ROOT / "weekly_scenes").mkdir(exist_ok=True)
    for i, scene in enumerate(ep["scenes"], 1):
        (ROOT / "weekly_scenes" / f"w{i}.png").write_bytes(cf_image(scene["image_prompt"]))
        print("image", i, "ok")

    # 5. Assemble: blurred-pad 1920x1080 Ken Burns segments + crossfades + subs.
    frames = int(round(seg * 30))
    for i in range(1, n + 1):
        subprocess.run(["ffmpeg", "-y", "-v", "error",
            "-i", str(ROOT / f"weekly_scenes/w{i}.png"), "-vf",
            "split[a][b];[a]scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1920:1080,boxblur=25[bg];[b]scale=1080:1080[fg];"
            "[bg][fg]overlay=(W-w)/2:0,"
            f"zoompan=z='min(1+0.08*on/{frames - 1},1.08)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            str(ROOT / f"wseg{i}.mp4")], check=True)
    fx, prev, off = [], "0:v", 0.0
    for i in range(1, n):
        off += seg - fade
        fx.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={fade}:offset={off:.3f}[x{i}]")
        prev = f"x{i}"
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080",
           "WrapStyle: 0", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           f"Style: Default,{STYLE}", "", "[Events]",
           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for i, s in enumerate(ep["scenes"]):
        ass.append(f"Dialogue: 0,{ts(i * (seg - fade) + 0.25)},{ts((i + 1) * (seg - fade) - 0.25)},Default,,0,0,0,,{s['narration']}")
    (ROOT / "weekly.ass").write_text("\n".join(ass))
    fx.append(f"[{prev}]subtitles=weekly.ass:fontsdir={FONTDIR}[vout]")
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for i in range(1, n + 1):
        cmd += ["-i", str(ROOT / f"wseg{i}.mp4")]
    cmd += ["-i", str(ROOT / "weekly_voice_clean.wav")]
    import datetime as _dt
    music, music_title = music_lib.pick(_dt.date.today().isocalendar()[1] * 2 + (1 if arc_dir.name == "arc2" else 0))
    print("music:", music_title)
    if music is not None and music.exists():
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        cmd += ["-filter_complex", ";".join(fx) + f";[{n}:a][{n+1}:a]amix=inputs=2:duration=first:normalize=0:weights=1 0.05,loudnorm=I=-14:TP=-1.5[aout]",
                "-map", "[vout]", "-map", "[aout]", "-shortest"]
    else:
        cmd += ["-filter_complex", ";".join(fx), "-map", "[vout]", "-map", f"{n}:a",
                "-af", "loudnorm=I=-14:TP=-1.5", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(ROOT / "weekly_final.mp4")]
    subprocess.run(cmd, check=True)
    print("built", ROOT / "weekly_final.mp4")

    # 6. Upload (public, long-form, not made for kids).
    body = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=body), timeout=60) as r:
        tok = json.load(r)["access_token"]
    video = (ROOT / "weekly_final.mp4").read_bytes()
    meta = json.dumps({"snippet": {
            "title": f"{ep['title']} | الحكاية الكاملة | حكايات بسبوسة",
            "description": (f"الحكاية الكاملة من حكايات بسبوسة (الأجزاء {parts[0]}-{parts[-1]})\n"
                            + ep.get("cliffhanger", "") + music_lib.attribution(music_title) +
                            "\n#بسبوسة #قصص_قطط #حكايات_بسبوسة #قصص_مصورة"),
            "categoryId": "24",
            "tags": ["بسبوسة", "حكايات بسبوسة", "قصص قطط", "قصص مصورة", "قصص اطفال", "حكايات"]},
        "status": ({"privacyStatus": "private", "publishAt": os.environ["PUBLISH_AT"],
                    "selfDeclaredMadeForKids": False} if os.environ.get("PUBLISH_AT")
                   else {"privacyStatus": "public", "selfDeclaredMadeForKids": False})}).encode()
    init = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=meta, method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(video))})
    with urllib.request.urlopen(init, timeout=60) as r:
        session_uri = r.headers["Location"]
    put = urllib.request.Request(session_uri, data=video, method="PUT",
                                 headers={"Content-Type": "video/mp4"})
    with urllib.request.urlopen(put, timeout=1800) as r:
        vid = json.load(r)["id"]
    print("uploaded long-form:", f"https://youtu.be/{vid}",
          "scheduled for " + os.environ["PUBLISH_AT"] if os.environ.get("PUBLISH_AT") else "public")
    try:
        make_thumb(ep, arc_dir.name)
        req = urllib.request.Request(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
            data=(ROOT / "weekly_thumb.jpg").read_bytes(), method="POST",
            headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"})
        urllib.request.urlopen(req, timeout=120).read()
        print("custom thumbnail set")
    except Exception as e:
        print("thumbnail failed (non-fatal):", e)

    wstate["compiled_upto_" + arc_dir.name] = max(parts)
    wstate["video_" + arc_dir.name] = vid
    (ROOT / "weekly_state.json").write_text(json.dumps(wstate, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
