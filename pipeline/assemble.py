"""Assemble the Short: per-scene Ken Burns zoom, crossfades, subtitles, voice.

Subtitle style fix vs the first preview: font 54 and 90px side margins so
long lines never clip the frame edges (scenes 1 and 6 clipped at 62/70).
"""
import json, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTDIR = "/usr/share/fonts/truetype/noto"
STYLE = ("Noto Naskh Arabic,72,&H00FFFFFF,&H000000FF,&H00141414,&H96000000,"
         "0,0,0,0,100,100,0,0,1,4,1,2,90,90,220,1")
# Big top-of-frame hook text for the first 2 seconds (yellow, bold, outlined).
HOOK_STYLE = ("Noto Naskh Arabic,130,&H0000D7FF,&H000000FF,&H00141414,&H96000000,"
              "1,0,0,0,100,100,0,0,1,5,2,8,60,60,300,1")

def ts(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"0:{int(m):02d}:{s:05.2f}"

def wav_duration(path: pathlib.Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())

def main() -> None:
    ep = json.loads((ROOT / "episode.json").read_text())
    scenes = sorted((ROOT / "scenes").glob("scene*.png"))
    n = len(scenes)
    # Retention: scene 1 is SHORTER with a fast punch-in zoom - the first 3
    # seconds decide whether the viewer stays, so the opening moves fast.
    seg, seg1, fade = 6.267, 3.2, 0.5
    # The video must NEVER end before the voice: extend the last scene so the
    # final line finishes, then hold a beat with a soft fade-out.
    voice = ROOT / "voice_clean.wav"
    voice_dur = wav_duration(voice) if voice.exists() else 0.0
    durs = [seg1] + [seg] * (n - 1)
    if voice_dur and n > 1:
        # Viral Short length 28-36s: spread scenes evenly over the voice.
        target = voice_dur + 1.2
        rest = max(3.5, (target - seg1 + (n - 1) * fade) / (n - 1))
        durs = [seg1] + [rest] * (n - 1)
    base = sum(durs) - (n - 1) * fade
    last_extra = max(0.0, voice_dur + 1.2 - base)  # 1.2s outro hold
    for i, img in enumerate(scenes, 1):
        d = durs[i - 1] + (last_extra if i == n else 0.0)
        frames = int(round(d * 30)) + 1
        if i == 1:
            # Punch-in: start already zoomed, move fast (high energy opening).
            zoom = "z='min(1.12+0.14*on/" + str(frames - 1) + ",1.26)'"
        else:
            zoom = "z='min(1+0.10*on/" + str(frames - 1) + ",1.10)'"
        # Single input frame + zoompan d=<frames>: 'on' then counts 0..frames-1
        # once, so the zoom never resets (looping input resets 'on' per frame).
        subprocess.run(["ffmpeg", "-y", "-v", "error",
            "-i", str(img), "-vf",
            "scale=3840:3840:force_original_aspect_ratio=increase,crop=2160:3840,zoompan=" + zoom + ":x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            str(ROOT / f"seg{i}.mp4")], check=True)
    # Crossfade chain. The last segment's extra length only extends the tail.
    total = base + last_extra
    fx, prev, off = [], "0:v", 0.0
    for i in range(1, n):
        off += durs[i - 1] - fade
        out = f"x{i}"
        fx.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={fade}:offset={off:.3f}[{out}]")
        prev = out
    subs = build_ass(ep, durs, fade)
    fx.append(f"[{prev}]subtitles={subs}:fontsdir={FONTDIR},fade=t=out:st={total - 0.7:.2f}:d=0.7[vout]")
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for i in range(1, n + 1):
        cmd += ["-i", str(ROOT / f"seg{i}.mp4")]
    if (ROOT / "voice_clean.wav").exists():
        cmd += ["-i", str(ROOT / "voice_clean.wav")]
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        import music as music_lib
        music, ep["music"] = music_lib.pick(int(ep.get("part", 0)) + (3 if os.environ.get("ARC_DIR") == "arc2" else 0))
        if music is not None and music.exists():
            cmd += ["-stream_loop", "-1", "-i", str(music)]
            cmd += ["-filter_complex", ";".join(fx) + f";[{n}:a][{n+1}:a]amix=inputs=2:duration=first:normalize=0:weights=1 0.05,apad,atrim=0:{total:.2f},afade=t=out:st={total - 0.9:.2f}:d=0.9,loudnorm=I=-14:TP=-1.5[aout]",
                    "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.2f}"]
        else:
            cmd += ["-filter_complex", ";".join(fx) + f";[{n}:a]apad,atrim=0:{total:.2f},afade=t=out:st={total - 0.9:.2f}:d=0.9,loudnorm=I=-14:TP=-1.5[aout]",
                    "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.2f}"]
    else:
        cmd += ["-filter_complex", ";".join(fx), "-map", "[vout]"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(ROOT / "episode_final.mp4")]
    subprocess.run(cmd, check=True)
    ep["duration_s"] = round(total, 1)
    (ROOT / "episode.json").write_text(json.dumps(ep, ensure_ascii=False, indent=2))
    st_path = ROOT / os.environ.get("STORY_STATE", "story_state.json")
    if st_path.exists():
        st = json.loads(st_path.read_text())
        st["last_duration_s"] = ep["duration_s"]
        st["last_story_type"] = ep.get("story_type")
        # Recorded so the review agent can correlate retention with hook style.
        st["last_hook_style"] = ep.get("hook_style")
        st_path.write_text(json.dumps(st, ensure_ascii=False, indent=2))
    print("built", ROOT / "episode_final.mp4", f"({total:.1f}s)")

def build_ass(ep, durs, fade) -> str:
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             f"Style: Default,{STYLE}", f"Style: Hook,{HOOK_STYLE}", "",
             "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    hook = ep.get("hook_text")
    if hook:
        # On screen from frame 0 through the punch-in (the 3-second decision window).
        lines.append(f"Dialogue: 1,{ts(0.0)},{ts(2.60)},Hook,,0,0,0,,{hook}")
    start = 0.0
    for i, s in enumerate(ep["scenes"]):
        end = start + durs[i] - (fade if i < len(durs) - 1 else 0.0)
        lines.append(f"Dialogue: 0,{ts(start + 0.25)},{ts(end - 0.25)},Default,,0,0,0,,{s['narration']}")
        start = end  # next scene starts where this one's crossfade ends
    p = ROOT / "episode.ass"
    p.write_text("\n".join(lines))
    return str(p)

if __name__ == "__main__":
    sys.exit(main())
