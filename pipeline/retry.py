"""Quality over punctuality: never ship a weaker episode to hit a slot.

Gemini (script, voice) is retried with spacing until a deadline that leaves
time to finish the build before the slot's publishAt. If it is still down at
the deadline the run FAILS (exit 1, message starts with HOLD). A failed run
does not count for the per-slot guard, so a later fire retries; once a slot is
too close, slot.py targets the next slot instead (the slot is skipped).
Fallbacks (Cloudflare script, edge-tts) exist only behind ALLOW_WEAK_FALLBACK=1.
"""
import datetime as dt, os, sys, time


class Hold(SystemExit):
    pass


def deadline(reserve_s: int, cap_s: int) -> float:
    """Epoch seconds until which retrying is allowed."""
    end = time.time() + cap_s
    at = os.environ.get("PUBLISH_AT")
    if at:
        pub = dt.datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp()
        end = min(end, pub - reserve_s)
    return end


def call(fn, label: str, reserve_s: int = 1500, cap_s: int = 10800, spacing_s: int = 240):
    """Call fn() until it returns; fn may raise. Waits spacing_s between rounds."""
    end = deadline(reserve_s, cap_s)
    n = 0
    while True:
        n += 1
        try:
            return fn()
        except Exception as e:
            print(f"{label}: round {n} failed: {e}", flush=True)
        if time.time() + spacing_s > end:
            print(f"HOLD: {label} still failing after {n} rounds; not shipping a weaker episode "
                  f"(a later run will retry or the slot is skipped)", flush=True)
            raise Hold(1)
        time.sleep(spacing_s)
