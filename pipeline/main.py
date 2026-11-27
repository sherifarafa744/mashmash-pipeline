import subprocess, sys, pathlib, os
HERE = pathlib.Path(__file__).parent
for step in ["vote.py", "gen_script.py", "gen_voice.py", "gen_images.py", "assemble.py", "loop_check.py", "gen_thumbnail.py", "upload.py"]:
    if step == "upload.py" and os.environ.get("GATE") == "1":
        subprocess.run([sys.executable, str(HERE / "gate.py")], check=True)
    print("==", step, flush=True)
    subprocess.run([sys.executable, str(HERE / step)], check=True)
