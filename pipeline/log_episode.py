"""Append one line per episode to episode_log.jsonl: opening type, length, publish hour."""
import json, os, pathlib, datetime as dt
ROOT = pathlib.Path(__file__).resolve().parent.parent
ep = json.loads((ROOT / "episode.json").read_text())
at = os.environ.get("PUBLISH_AT", "")
row = {"logged_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
       "arc": os.environ.get("ARC_DIR"), "part": ep.get("part"), "title": ep.get("title"),
       "opening_type": ep.get("hook_style"), "opening_line": ep.get("opening_line"),
       "opening_words": len((ep.get("opening_line") or "").split()),
       "duration_s": ep.get("duration_s"), "scenes": len(ep.get("scenes", [])),
       "story_type": ep.get("story_type"), "publish_at": at, "voice_s": ep.get("voice_s"), "voice_tempo": ep.get("voice_tempo"), "language_style": ep.get("language_style") or "v1_egyptian", "motion_style": ep.get("motion_style") or "v1_zoom", "sfx_at_s": ep.get("sfx_at_s"), "caption_style": ep.get("caption_style") or "v1_sentence", "voice_style": ep.get("voice_style") or "v1_flat", "voice_name": ep.get("voice_name") or "Charon", "upload_mode": os.environ.get("UPLOAD_MODE") or "scheduled",
       "publish_hour_utc": int(at[11:13]) if at else None,
       "publish_hour_cairo": (int(at[11:13]) + 2) % 24 if at else None,
       "hook_mode": ep.get("hook_mode", "default"), "build_tag": ep.get("build_tag"), "opening_sfx": ep.get("opening_sfx", False), "tight_cut": ep.get("tight_cut", False), "no_top_hook": ep.get("no_top_hook", False), "danger_first": bool(ep.get("danger_first")), "format_issues": ep.get("format_issues", [])}
with open(ROOT / "episode_log.jsonl", "a") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
print("logged:", row)
