"""Loop check: compares the first and last frame of episode_final.mp4 (SSIM + brightness)
and the audio level at both ends. Writes loop_ok etc. into episode.json. Never fails the build."""
import json, pathlib, re, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
def run(c):
    r = subprocess.run(c, capture_output=True, text=True); return r.stdout + r.stderr
try:
    v = ROOT / "episode_final.mp4"
    d = float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(v)]).strip())
    (ROOT/"loopcheck").mkdir(exist_ok=True)
    for n,t in (("first",0.0),("last",max(0,d-0.1))):
        run(["ffmpeg","-v","error","-y","-ss",f"{t:.2f}","-i",str(v),"-frames:v","1","-vf","scale=360:-1",str(ROOT/"loopcheck"/f"{n}.png")])
    o = run(["ffmpeg","-i",str(ROOT/"loopcheck/first.png"),"-i",str(ROOT/"loopcheck/last.png"),"-lavfi","ssim;[0:v][1:v]psnr","-f","null","-"])
    ssim = float(re.search(r"SSIM.*?All:([0-9.]+)", o).group(1))
    def luma(f):
        s = run(["ffmpeg","-i",f,"-vf","signalstats,metadata=print:key=lavfi.signalstats.YAVG","-f","null","-"])
        return float(re.findall(r"YAVG=([0-9.]+)", s)[-1])
    dl = abs(luma(str(ROOT/"loopcheck/first.png")) - luma(str(ROOT/"loopcheck/last.png")))
    def mean(args):
        s = run(["ffmpeg","-v","info"]+args+["-i",str(v),"-af","volumedetect","-f","null","-"])
        m = re.search(r"mean_volume: (-?[0-9.]+)", s); return float(m.group(1)) if m else -91.0
    a_end = mean(["-ss",f"{max(0,d-0.3):.2f}"]); a_start = mean(["-t","0.3"])
    ok = ssim >= 0.45 and dl < 25 and a_end > -40
    ep = json.loads((ROOT/"episode.json").read_text())
    ep.update({"loop_ssim": round(ssim,3), "loop_luma_diff": round(dl,1), "loop_audio_end_db": a_end, "loop_audio_start_db": a_start, "loop_ok": ok})
    (ROOT/"episode.json").write_text(json.dumps(ep, ensure_ascii=False, indent=2))
    print("LOOPCHECK", ep["loop_ssim"], ep["loop_luma_diff"], a_end, a_start, ok)
except Exception as e:
    print("loop check skipped:", e)
