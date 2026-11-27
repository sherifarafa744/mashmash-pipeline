"""Narration via Gemini TTS free tier.

Free tier (Nov 2026): 10 requests/day per TTS model, 3 RPM, 10K TPM.
flash-tts / flash-lite-tts / 2.5-flash-preview-tts have SEPARATE daily
buckets, so we batch the WHOLE episode into ONE request and split the
returned WAV at silence into per-scene lines.
Free-tier content is used by Google to improve its products; our content is
original fiction, no personal data.
"""
import base64, json, os, pathlib, subprocess, sys, time, urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
VOICE = os.environ.get("GEMINI_TTS_VOICE", "Charon")
EDGE_VOICE = os.environ.get("EDGE_TTS_VOICE", "ar-EG-ShakirNeural")
ROOT = pathlib.Path(__file__).resolve().parent.parent


def synthesize(text: str) -> bytes:
    body = json.dumps({
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}},
        },
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.load(r)
    return base64.b64decode(out["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])


def main() -> None:
    ep = json.loads((ROOT / "episode.json").read_text())
    beat = ep.get("beat_scene")  # 1-based scene holding the shock/twist beat
    lines = []
    for i, sc in enumerate(ep["scenes"], 1):
        # A short dramatic beat right before the shock line (TTS honors "..." and line breaks).
        lines.append(("...\n" if (not ep.get("celebration") and beat == i and i > 1) else "") + sc["narration"])
    full = "\n".join(lines)
    prefix = ("اقرأ بصوت فرحان ومحتفل، طاقة عيد من أول كلمة، وقفة قصيرة بين كل جملة:\n"
              if ep.get("celebration") else
              "أنت حكواتي أطفال بتحكي بحماس شديد وأداء تمثيلي: ابدأ فوراً بأول جملة بدون مقدمة وبنبرة صدمة وإثارة، "
              "ارفع الطاقة في لحظات الخطر والمفاجأة، خفّض صوتك شوية وقت التشويق، واعمل وقفة قصيرة جداً (نص ثانية) قبل جملة الصدمة، "
              "وخلّي الإيقاع سريع ومتنوع مش رتيب، وخلّي آخر جملة بنبرة سؤال مشوّق:\n")
    ep["voice_style"] = "v2_expressive_ducked"
    ep["voice_name"] = VOICE
    (ROOT / "episode.json").write_text(json.dumps(ep, ensure_ascii=False, indent=2))
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import retry
    pcm = None
    try:
        # Retry Gemini TTS over a long window; leave ~15 min for images + assembly.
        pcm = None if os.environ.get("FORCE_TTS_FALLBACK") else retry.call(
            lambda: synthesize(prefix + full), "voice", reserve_s=900, cap_s=7200, spacing_s=240)
    except SystemExit:
        if os.environ.get("ALLOW_WEAK_FALLBACK") != "1":
            raise
    if pcm is not None:
        (ROOT / "voice_full.pcm").write_bytes(pcm)
        # Gemini returns raw 24kHz s16le mono PCM; wrap then split at silence.
        subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                        "-i", "voice_full.pcm", "voice_full.wav"], cwd=ROOT, check=True)
    else:
        # Only with ALLOW_WEAK_FALLBACK=1 (off in the schedule): edge-tts ar-EG.
        print("ALLOW_WEAK_FALLBACK=1: edge-tts (ar-EG)")
        subprocess.run([sys.executable, "-m", "edge_tts", "--voice", EDGE_VOICE, "--rate=+8%",
                        "--text", full, "--write-media", "voice_edge.mp3"], cwd=ROOT, check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "voice_edge.mp3", "-ar", "24000", "-ac", "1",
                        "voice_full.wav"], cwd=ROOT, check=True)
        ep["voice"] = "edge-tts:" + EDGE_VOICE
        (ROOT / "episode.json").write_text(json.dumps(ep, ensure_ascii=False, indent=2))
    # Retention: trim LEADING silence too, so the first word lands at ~0s
    # (viewers decide in the first 3 seconds), then collapse long inner pauses.
    subprocess.run(["ffmpeg", "-y", "-i", "voice_full.wav", "-af",
                    "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,"
                    "silenceremove=stop_periods=-1:stop_duration=0.45:stop_threshold=-38dB:stop_silence=0.22",
                    "voice_clean.wav"], cwd=ROOT, check=True)
    # Length control: the expressive voice runs ~1.85 words/s. If the clean voice is
    # longer than 34.5s, time-stretch it (pitch kept) by at most 1.15x so the Short
    # lands at 28-36s. Celebrations are exempt.
    def dur(path):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, cwd=ROOT)
        return float(r.stdout.strip())
    d0 = dur(ROOT / "voice_clean.wav")
    tempo = 1.0
    if not ep.get("celebration") and d0 > 34.5:
        tempo = min(1.15, d0 / 34.5)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "voice_clean.wav", "-af", f"atempo={tempo:.3f}", "voice_fast.wav"],
                       cwd=ROOT, check=True)
        (ROOT / "voice_fast.wav").replace(ROOT / "voice_clean.wav")
        print(f"voice {d0:.1f}s too long: atempo {tempo:.3f} -> {dur(ROOT / 'voice_clean.wav'):.1f}s")
    ep["voice_tempo"] = round(tempo, 3)
    ep["voice_s"] = round(dur(ROOT / "voice_clean.wav"), 1)
    (ROOT / "episode.json").write_text(json.dumps(ep, ensure_ascii=False, indent=2))
    print("voice ready:", ROOT / "voice_clean.wav")


if __name__ == "__main__":
    sys.exit(main())
