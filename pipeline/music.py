"""Rotating background music: Kevin MacLeod tracks (incompetech.com, CC-BY 4.0).

music/tracks.json lists the tracks. pick(key) is deterministic (key % n) so an
episode keeps one track; attribution(title) is the exact line every upload
description must carry for the track used.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_TITLE = "Sneaky Snitch"

def tracks() -> list:
    p = ROOT / "music" / "tracks.json"
    return json.loads(p.read_text()) if p.exists() else []

def pick(key: int):
    """Return (path or None, title)."""
    t = tracks()
    try:  # config music_force: use one named track (keeps the rotation of other episodes unchanged)
        want = json.loads((ROOT / "config.json").read_text()).get("music_force")
    except Exception:
        want = None
    if want:
        for e in t:
            if e["title"] == want:
                return ROOT / e["file"], e["title"]
    t = [e for e in t if e["title"] != "Curse of the Scarab"]  # rotation unchanged: the new track is used only via music_force
    if not t:
        legacy = ROOT / "music.mp3"
        return (legacy if legacy.exists() else None), DEFAULT_TITLE
    e = t[key % len(t)]
    return ROOT / e["file"], e["title"]

def attribution(title: str) -> str:
    return (f"\nالموسيقى: {title} - Kevin MacLeod (incompetech.com)\n"
            "Licensed under Creative Commons: By Attribution 4.0\n"
            "https://creativecommons.org/licenses/by/4.0/")
