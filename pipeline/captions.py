"""Word-by-word (karaoke) captions: 3-4 word chunks, big, the spoken word highlighted.

Word timing: the voice is one WAV (no per-word timestamps from TTS), so we find
the sentence pauses with ffmpeg silencedetect and spread each sentence's words
over its speech span by letter count. Arabic is laid out by libass (RTL +
shaping); trailing '!' and other punctuation are dropped (they flip to the
wrong side under bidi) and only '؟' is kept, followed by a RLM mark.
"""
import re, subprocess

HI = "&H0000D7FF"   # highlight: yellow (BGR)
LO = "&H00FFFFFF"   # normal: white
RLM = "\u200f"
STRIP = re.compile(r"[!،,.…:;\"'«»()\-–—]+")


def ts(sec: float) -> str:
    sec = max(0.0, sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def sentences(ep) -> list:
    out = []
    for sc in ep["scenes"]:
        for part in re.split(r"(?<=[.!؟?!…])\s+", sc["narration"].strip()):
            words = [w for w in (STRIP.sub("", x) for x in part.split()) if w]
            if words:
                out.append(words)
    return out


def speech_span(wav, dur):
    """(speech_start, speech_end, [(pause_start, pause_end), ...]) from silencedetect."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(wav), "-af", "silencedetect=noise=-35dB:d=0.12",
                        "-f", "null", "-"], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    pauses = list(zip(starts, ends + [dur] * (len(starts) - len(ends))))
    s0, e1 = 0.0, dur
    if pauses and pauses[0][0] <= 0.05:
        s0 = pauses.pop(0)[1]
    if pauses and pauses[-1][1] >= dur - 0.05:
        e1 = pauses.pop()[0]
    return s0, e1, pauses


def word_times(ep, wav, dur):
    sents = sentences(ep)
    s0, e1, pauses = speech_span(wav, dur)
    need = len(sents) - 1
    if need > 0 and len(pauses) >= need:
        cut = sorted(sorted(pauses, key=lambda p: p[1] - p[0], reverse=True)[:need])  # longest pauses
        bounds, a = [], s0
        for p in cut:
            bounds.append((a, p[0])); a = p[1]
        bounds.append((a, e1))
    else:
        # fall back: spread all sentences over the speech span by letter count
        tot = sum(len("".join(s)) for s in sents) or 1
        bounds, a = [], s0
        for s in sents:
            d = (e1 - s0) * len("".join(s)) / tot
            bounds.append((a, a + d)); a += d
    out = []  # (word, start, end)
    for words, (a, b) in zip(sents, bounds):
        tot = sum(len(w) + 1 for w in words)
        t = a
        for w in words:
            d = (b - a) * (len(w) + 1) / tot
            out.append((w, t, t + d)); t += d
    return out


def build_events(ep, wav, dur, chunk=3):
    wt = word_times(ep, wav, dur)
    ev = []
    for i in range(0, len(wt), chunk):
        grp = wt[i:i + chunk]
        # avoid a lonely last word
        if len(wt) - (i + chunk) == 1:
            grp = wt[i:i + chunk + 1]
        nxt = wt[i + len(grp)][1] if i + len(grp) < len(wt) else min(dur, grp[-1][2] + 0.6)
        for k, (w, a, b) in enumerate(grp):
            end = grp[k + 1][1] if k + 1 < len(grp) else nxt
            text = " ".join((f"{{\\c{HI}&}}{x}{{\\c{LO}&}}" if j == k else x) for j, (x, _, _) in enumerate(grp))
            # RLM keeps neutral characters (spaces, tags) on the right side
            ev.append(f"Dialogue: 0,{ts(a)},{ts(end)},Cap,,0,0,0,,{RLM}{text}{RLM}")
        if i + len(grp) >= len(wt):
            break
    return ev


def beat_time(ep, wav, dur):
    """Start time (s) of the shock-beat scene's first word, or None."""
    b = ep.get("beat_scene")
    if not isinstance(b, int) or b < 2 or b > len(ep["scenes"]) or ep.get("celebration"):
        return None
    before = 0
    for sc in ep["scenes"][:b - 1]:
        before += len([w for w in (STRIP.sub("", x) for x in sc["narration"].split()) if w])
    wt = word_times(ep, wav, dur)
    return wt[before][1] if before < len(wt) else None
