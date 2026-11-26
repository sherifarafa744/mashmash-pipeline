"""Shock-beat sound effect, synthesized with ffmpeg (noise riser + low impact).
Generated from scratch, so there is no third-party licence to track."""
import subprocess

def make(path) -> None:
    fc = ("anoisesrc=d=0.3:c=pink:a=0.8:r=44100,highpass=f=600,afade=t=in:d=0.3,volume=0.55[w];"
          "anoisesrc=d=0.5:c=white:a=0.9:r=44100,lowpass=f=2600,afade=t=out:d=0.35,volume=0.8[h1];"
          "sine=f=55:d=0.5:r=44100,afade=t=out:d=0.5,volume=1.4[h2];"
          "[h1][h2]amix=inputs=2:normalize=0,adelay=300|300[hit];"
          "[w][hit]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,alimiter=limit=0.9[o]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-filter_complex", fc, "-map", "[o]", "-ar", "44100", str(path)], check=True)
