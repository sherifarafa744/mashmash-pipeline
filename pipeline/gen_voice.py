"""Narration via Gemini TTS free tier.

Free tier (Nov 2026): 10 requests/day per TTS model, 3 RPM, 10K TPM.
flash-tts / flash-lite-tts / 2.5-flash-preview-tts have SEPARATE daily
buckets, so we batch the WHOLE episode into ONE request and split the
returned WAV at silence into per-scene lines.
Free-tier content is used by Google to improve its products; our content is
original fiction, no personal data.
"""
import base64, json, os, pathlib, subprocess, sys, urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
VOICE = os.environ.get("GEMINI_TTS_VOICE", "Charon")
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
    full = "\n".join(s["narration"] for s in ep["scenes"])
    pcm = synthesize("ابدأ فوراً بأول جملة بدون أي مقدمة أو تردد، اقرأ كحكوتي بحماس عالي من أول كلمة، وقفة قصيرة بين كل جملة:\n" + full)
    (ROOT / "voice_full.pcm").write_bytes(pcm)
    # Gemini returns raw 24kHz s16le mono PCM; wrap then split at silence.
    subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                    "-i", "voice_full.pcm", "voice_full.wav"], cwd=ROOT, check=True)
    # Retention: trim LEADING silence too, so the first word lands at ~0s
    # (viewers decide in the first 3 seconds), then collapse long inner pauses.
    subprocess.run(["ffmpeg", "-y", "-i", "voice_full.wav", "-af",
                    "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,"
                    "silenceremove=stop_periods=-1:stop_duration=0.45:stop_threshold=-38dB",
                    "voice_clean.wav"], cwd=ROOT, check=True)
    print("voice ready:", ROOT / "voice_clean.wav")


if __name__ == "__main__":
    sys.exit(main())
