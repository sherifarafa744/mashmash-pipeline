"""Build thumb.jpg: scene 1 frame + big Arabic title, shaped via libass.

drawtext does not shape Arabic; burning a one-line ASS does. Requires the
channel to be phone-verified for thumbnails.set to succeed (upload.py).
"""
import json, pathlib, subprocess, sys, textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTDIR = "/usr/share/fonts/truetype/noto"

def main() -> None:
    ep = json.loads((ROOT / "episode.json").read_text())
    # Thumbnail frame: the shock-beat scene (clear single moment), else scene 2. Scene 1 is
    # a busy opening (danger plus several characters) and read as confusing.
    n = len(ep.get("scenes", [])) or 5
    idx = ep.get("beat_scene")
    idx = idx if isinstance(idx, int) and 2 <= idx <= n else min(2, n)
    scene1 = ROOT / "scenes" / f"scene{idx}.png"
    if not scene1.exists():
        scene1 = ROOT / "scenes" / "scene1.png"
    import re
    # Emoji render as tofu boxes in Noto Naskh Arabic - strip them from the burned title.
    title = re.sub(r"[^0-9A-Za-z\u0600-\u06FF\u0750-\u077F\s?!.،:؛\-]", "", ep["title"].replace(" | بسبوسة", "")).strip()
    ass = ROOT / "thumb.ass"
    ass.write_text("\n".join([
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Noto Naskh Arabic,64,&H0000FFFF,&H000000FF,&H00141414,&H96000000,0,0,0,0,100,100,0,0,1,5,1,2,60,60,60,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{title}"]))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", "1", "-i", str(scene1),
        "-vf", f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,subtitles={ass}:fontsdir={FONTDIR}",
        "-frames:v", "1", "-q:v", "3", str(ROOT / "thumb.jpg")], check=True)
    print("thumbnail:", ROOT / "thumb.jpg")

if __name__ == "__main__":
    sys.exit(main())
