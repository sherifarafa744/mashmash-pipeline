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

# Karaoke caption line (3 words at a time, active word yellow): big, bold, thick outline.
CAP_STYLE = ("Cap,Noto Naskh Arabic,92,&H00FFFFFF,&H000000FF,&H00141414,&H96000000,"
             "1,0,0,0,100,100,0,0,1,7,2,2,60,60,330,1")

def ts(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"0:{int(m):02d}:{s:05.2f}"

def wav_duration(path: pathlib.Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())

try:
    _C = json.loads((ROOT / "config.json").read_text())
except Exception:
    _C = {}
OPEN_SFX = bool(_C.get("opening_sfx"))
TAIL = 0.35 if _C.get("tight_cut") else 1.2
NO_TOP_HOOK = bool(_C.get("no_top_hook"))
FADE_A = 0.3 if _C.get("tight_cut") else 0.9
FADE_V = 0.3 if _C.get("tight_cut") else 0.7
_FIN = (_C.get("finale") or {}).get(os.environ.get("ARC_DIR", ""))  # finale part number for this arc: no loop, normal fade out
LOOP_END = bool(_C.get("loop_end"))
LOOP_REUSE = bool(_C.get("loop_reuse_first"))
MUSIC_GAP = bool(_C.get("music_gap"))
if LOOP_END:
    FADE_V = 0.0  # hard end on the last frame (no fade to black) so it flows back into frame 1
    FADE_A = 0.08


def main() -> None:
    global LOOP_END, LOOP_REUSE, FADE_V, FADE_A
    ep = json.loads((ROOT / "episode.json").read_text())
    if _FIN and _FIN == ep.get("part"):
        LOOP_END = LOOP_REUSE = False
        FADE_V, FADE_A = (0.3, 0.9) if not _C.get("tight_cut") else (0.3, 0.3)
        ep["finale"] = True
    scenes = [ROOT / "scenes" / f"scene{i}.png" for i in range(1, len(ep["scenes"]) + 1)]  # exactly the episode's scenes, never stale extras
    assert all(x.exists() for x in scenes), "missing scene image"
    if LOOP_REUSE and len(scenes) > 2:
        scenes[-1] = scenes[0]  # loop: the last shot is the opening shot again (same composition as frame 1)
    n = len(scenes)
    # Retention: scene 1 is SHORTER with a fast punch-in zoom - the first 3
    # seconds decide whether the viewer stays, so the opening moves fast.
    seg, seg1, fade = 6.267, 3.2, 0.3
    # The video must NEVER end before the voice: extend the last scene so the
    # final line finishes, then hold a beat with a soft fade-out.
    voice = ROOT / "voice_clean.wav"
    voice_dur = wav_duration(voice) if voice.exists() else 0.0
    durs = [seg1] + [seg] * (n - 1)
    if voice_dur and n > 1:
        # Viral Short length 28-36s: spread scenes evenly over the voice.
        target = voice_dur + TAIL
        rest = max(3.5, (target - seg1 + (n - 1) * fade) / (n - 1))
        durs = [seg1] + [rest] * (n - 1)
    base = sum(durs) - (n - 1) * fade
    last_extra = max(0.0, voice_dur + TAIL - base)  # outro hold (1.2s default, 0.35s with tight_cut)
    for i, img in enumerate(scenes, 1):
        d = durs[i - 1] + (last_extra if i == n else 0.0)
        total_frames = int(round(d * 30)) + 1
        # Quick cuts: a hard cut every ~2-3s inside each scene (same image, alternating
        # zoom-in and side pan), so the picture keeps moving like a viral Short.
        k = 1 if d < 3.4 and i != 1 else (3 if d >= 7.4 else 2)
        if i == 1:
            k = 2
        cuts = [int(total_frames * j / k) for j in range(k + 1)]
        chains, labels = [], []
        for j in range(k):
            fr = max(8, cuts[j + 1] - cuts[j])
            if i == 1 and j == 0:
                zoom = f"z='min(1.12+0.14*on/{fr - 1},1.26)':x='iw/2-(iw/zoom/2)'"       # punch-in
            elif (j + i) % 2 == 0:
                zoom = f"z='min(1+0.12*on/{fr - 1},1.12)':x='iw/2-(iw/zoom/2)'"          # slow zoom-in
            else:
                frac = f"on/{fr - 1}" if i % 2 else f"(1-on/{fr - 1})"
                zoom = f"z=1.22:x='(iw-iw/zoom)*{frac}'"                                  # side pan
            chains.append(f"[s{j}]zoompan={zoom}:y='ih/2-(ih/zoom/2)':d={fr}:s=1080x1920:fps=30,format=yuv420p[c{j}]")
            labels.append(f"[c{j}]")
        fc = (f"[0:v]scale=3840:3840:force_original_aspect_ratio=increase,crop=2160:3840,split={k}"
              + "".join(f"[s{j}]" for j in range(k)) + ";" + ";".join(chains) + ";"
              + "".join(labels) + f"concat=n={k}:v=1:a=0[v]")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(img), "-filter_complex", fc, "-map", "[v]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", str(ROOT / f"seg{i}.mp4")], check=True)
    ep["motion_style"] = "v2_cuts_pan_sfx"
    # Crossfade chain. The last segment's extra length only extends the tail.
    total = base + last_extra
    fx, prev, off = [], "0:v", 0.0
    for i in range(1, n):
        off += durs[i - 1] - fade
        out = f"x{i}"
        fx.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={fade}:offset={off:.3f}[{out}]")
        prev = out
    cap_events = None
    ep["caption_style"] = "v1_sentence"
    try:
        cap_mode = json.loads((ROOT / "config.json").read_text()).get("captions", "sentence")
    except Exception:
        cap_mode = "sentence"
    if voice_dur and cap_mode in ("karaoke", "sentence_timed"):
        try:
            sys.path.insert(0, str(pathlib.Path(__file__).parent))
            import captions
            if cap_mode == "karaoke":
                cap_events = captions.build_events(ep, voice, voice_dur)
                nwords = sum(len(x) for x in captions.sentences(ep))
                if not cap_events or len(cap_events) < nwords:
                    raise RuntimeError(f"caption events {len(cap_events)} < words {nwords}")
                ep["caption_style"] = "v2_karaoke_3w"
            else:
                cap_events, sb = captions.sentence_events(ep, voice, voice_dur)
                if not cap_events:
                    raise RuntimeError("no caption events")
                ep["caption_style"] = "v3_sentence_timed"
                ep["caption_sentence_starts"] = [round(x[1], 2) for x in sb]
        except Exception as e:  # never lose the episode over captions: old sentence captions
            print("timed captions failed, using per-scene sentence captions:", e)
            cap_events = None
            ep["caption_style"] = "v1_sentence"
    subs = build_ass(ep, durs, fade, cap_events)
    _fv = f",fade=t=out:st={total - FADE_V:.2f}:d={FADE_V}" if FADE_V > 0 else ""
    fx.append(f"[{prev}]subtitles={subs}:fontsdir={FONTDIR}{_fv}[vout]")
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
            # Short synthesized impact right at the shock beat (if the script marked one).
            beat = None
            try:
                import captions, sfx
                beat = captions.beat_time(ep, voice, voice_dur)
                if beat is not None:
                    sfx.make(ROOT / "sfx_hit.wav")
                    cmd += ["-i", str(ROOT / "sfx_hit.wav")]
                    if OPEN_SFX:
                        cmd += ["-i", str(ROOT / "sfx_hit.wav")]
            except Exception as e:
                print("sfx skipped:", e)
                beat = None
            mix_sfx = ""
            last = "[vo2][mduck]amix=inputs=2:duration=longest:normalize=0:weights=1 1[mx]"  # music keeps playing to the very end (no silent tail)
            if beat is not None:
                ms = max(0, int((beat - 0.3) * 1000))
                last += f";[{n+2}:a]adelay={ms}|{ms},volume=0.4[sx];[mx][sx]amix=inputs=2:duration=first:normalize=0:weights=1 1[mx2]"
                mx = "[mx2]"
                ep["sfx_at_s"] = round(beat, 2)
                if OPEN_SFX:
                    # Impact at the very start (first frame), same synthesized hit.
                    last += f";[{n+3}:a]atrim=start=0.22,asetpts=PTS-STARTPTS,volume=0.35[so];[mx2][so]amix=inputs=2:duration=first:normalize=0:weights=1 1[mx3]"
                    mx = "[mx3]"
                    ep["opening_sfx"] = True
            else:
                mx = "[mx]"
            # Music ducks under the voice (sidechain), lower base level than the
            # old constant 0.05 mix; music comes back up in the pauses.
            old_mix = _C.get("music_mix") == "old"  # fallback: the previously tested quieter mix
            MIX_VOL, MIX_THR, MIX_RATIO = (0.062, 0.02, 10) if old_mix else (0.22, 0.03, 3)
            gap = ""
            if MUSIC_GAP and beat is not None and beat > 1.5:
                gap = f",volume=0:enable='between(t,{beat-0.7:.2f},{beat-0.1:.2f})'"  # silence beat before the tension moment
                ep["music_gap"] = True
            cmd += ["-filter_complex", ";".join(fx) + f";[{n}:a]aresample=44100,aformat=channel_layouts=stereo,asplit=2[vo1x][vo2];[vo1x]anull[vo1];[{n+1}:a]aresample=44100,aformat=channel_layouts=stereo,volume={MIX_VOL}{gap}[mus];"
                    f"[mus][vo1]sidechaincompress=threshold={MIX_THR}:ratio={MIX_RATIO}:attack=15:release=400:makeup=1[mduck];"
                    f"{last};{mx}apad,atrim=0:{total:.2f},afade=t=out:st={total - FADE_A:.2f}:d={FADE_A},loudnorm=I=-14:TP=-1.5[aout]",
                    "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.2f}"]
        else:
            cmd += ["-filter_complex", ";".join(fx) + f";[{n}:a]apad,atrim=0:{total:.2f},afade=t=out:st={total - FADE_A:.2f}:d={FADE_A},loudnorm=I=-14:TP=-1.5[aout]",
                    "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.2f}"]
    else:
        cmd += ["-filter_complex", ";".join(fx), "-map", "[vout]"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(ROOT / "episode_final.mp4")]
    subprocess.run(cmd, check=True)
    if TAIL < 1.0: ep["tight_cut"] = True
    if NO_TOP_HOOK: ep["no_top_hook"] = True
    if LOOP_END: ep["loop_end"] = True
    if LOOP_REUSE: ep["loop_reuse_first"] = True
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

def build_ass(ep, durs, fade, cap_events=None) -> str:
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             f"Style: Default,{STYLE}", f"Style: Hook,{HOOK_STYLE}", f"Style: {CAP_STYLE}", "",
             "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    hook = ep.get("hook_text")
    if hook and not NO_TOP_HOOK:
        # On screen from frame 0 through the punch-in (the 3-second decision window).
        lines.append(f"Dialogue: 1,{ts(0.0)},{ts(2.60)},Hook,,0,0,0,,{hook}")
    if cap_events:
        lines.extend(cap_events)
    start = 0.0
    for i, s in enumerate([] if cap_events else ep["scenes"]):
        end = start + durs[i] - (fade if i < len(durs) - 1 else 0.0)
        lines.append(f"Dialogue: 0,{ts(start + 0.25)},{ts(end - 0.25)},Default,,0,0,0,,{s['narration']}")
        start = end  # next scene starts where this one's crossfade ends
    p = ROOT / "episode.ass"
    p.write_text("\n".join(lines))
    return str(p)

if __name__ == "__main__":
    sys.exit(main())
