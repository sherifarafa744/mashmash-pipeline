"""Optional gate before upload (GATE=1): push a preview branch, wait for tag go-<run> or nogo-<run>."""
import os, subprocess, sys, time, shutil, glob, pathlib
rid = os.environ["GITHUB_RUN_ID"]; repo = os.environ["GITHUB_REPOSITORY"]
def sh(c, check=True): return subprocess.run(c, shell=True, check=check, capture_output=True, text=True)
br = sh("git rev-parse --abbrev-ref HEAD").stdout.strip()
os.makedirs("/tmp/pv", exist_ok=True)
for f in ["episode_final.mp4", "episode.json", "thumb.jpg"] + glob.glob("loopcheck/*.png") + glob.glob("scenes/scene*.png"):
    if os.path.exists(f): shutil.copy(f, "/tmp/pv/")
sh('git config user.name mashmash-bot; git config user.email bot@users.noreply.github.com')
sh(f"git checkout -q -b preview-{rid}")
os.makedirs("preview", exist_ok=True)
sh("cp /tmp/pv/* preview/ && git add -f preview && git commit -qm preview && git push -q origin HEAD")
sh(f"git checkout -q {br}")
print(f"preview ready on branch preview-{rid}; waiting for go-{rid} / nogo-{rid}", flush=True)
for _ in range(400):
    if sh(f"gh api repos/{repo}/git/ref/tags/go-{rid}", check=False).returncode == 0: print("GO"); sys.exit(0)
    if sh(f"gh api repos/{repo}/git/ref/tags/nogo-{rid}", check=False).returncode == 0: print("NOGO"); sys.exit(1)
    time.sleep(20)
print("no decision in time"); sys.exit(1)
