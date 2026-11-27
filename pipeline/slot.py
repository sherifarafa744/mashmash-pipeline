"""Publish-slot math. Slots are 09/12/15/18 UTC (11/14/17/20 Africa/Cairo).
Episodes are built ahead of time and uploaded PRIVATE with a YouTube publishAt
equal to the next slot, so GitHub scheduler delays never move the publish time.

  python pipeline/slot.py target [ISO_NOW]   -> prints target ISO (UTC, Z)
  python pipeline/slot.py guard              -> prints "skip" if a successful run
                                                already served this target slot
Lead: build fires start 4h before a slot (05/08/11/14 UTC); a fire targets the first slot more than BUFFER away.
"""
import datetime as dt, json, os, sys, urllib.request

SLOT_HOURS = (9, 12, 15, 18)
BUFFER = 2 * 3600  # target = first slot more than 2h away; builds start ~4h ahead
# Runs before the build-ahead switch served slots in the old way; ignore them.
PAUSE_UNTIL = "2026-11-28T10:00:00Z"
SINCE = "2026-11-25T23:11:00Z"

def target(now: dt.datetime) -> dt.datetime:
    earliest = now + dt.timedelta(seconds=BUFFER)
    for day in (0, 1):
        d = (earliest + dt.timedelta(days=day)).date()
        for h in SLOT_HOURS:
            t = dt.datetime(d.year, d.month, d.day, h, tzinfo=dt.timezone.utc)
            if t > earliest:
                return t
    raise SystemExit("no slot")

def iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def parse(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))

def main() -> None:
    cmd = sys.argv[1]
    if cmd == "target":
        now = parse(sys.argv[2]) if len(sys.argv) > 2 else dt.datetime.now(dt.timezone.utc)
        print(iso(target(now)))
    elif cmd == "arcfor":  # arcfor 2 -> 3 once the arc2 finale has run and arc3 is set up
        arc = sys.argv[2]
        try:
            cfg = json.load(open("config.json"))
            fin = (cfg.get("finale") or {}).get("arc" + arc)
            ep = json.load(open(f"story_state_arc{arc}.json")).get("episode", 0)
            nxt = cfg.get("successor", {}).get("arc" + arc)
            if fin and ep >= fin and nxt:
                arc = nxt
        except Exception:
            pass
        print(arc)
    elif cmd == "guard":
        if os.environ.get("GITHUB_EVENT_NAME") == "schedule" and dt.datetime.now(dt.timezone.utc) < parse(PAUSE_UNTIL):
            print("skip")  # scheduled builds paused until the Gemini/Cloudflare quotas reset (user decision)
            return
        arc = os.environ.get("ARC_NUM", "")
        try:  # a new storyline stays off until the user approves it (config arc3_approved)
            if arc == "3" and not json.load(open("config.json")).get("arc3_approved"):
                print("skip")
                return
        except Exception:
            pass
        try:  # a storyline whose finale already ran must not continue: its slots stay empty until a new story is set up
            fin = (json.load(open("config.json")).get("finale") or {}).get("arc" + arc)
            ep = json.load(open(f"story_state_arc{arc}.json")).get("episode", 0)
            if fin and ep >= fin:
                print("skip")
                return
        except Exception:
            pass
        if os.environ.get("FORCE") == "1":
            print("run")
            return
        wf = os.environ.get("WORKFLOW_FILE", "daily.yml")
        me = int(os.environ["GITHUB_RUN_ID"])
        want = target(dt.datetime.now(dt.timezone.utc))
        req = urllib.request.Request(
            f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/actions/workflows/{wf}/runs?status=completed&per_page=30",
            headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"]})
        runs = json.load(urllib.request.urlopen(req, timeout=60)).get("workflow_runs", [])
        for r in runs:
            if r["conclusion"] == "success" and r.get("event") != "workflow_dispatch" and r["id"] != me and parse(r["created_at"]) >= parse(SINCE) and target(parse(r["created_at"])) == want:
                print("skip")
                return
        print("run")

if __name__ == "__main__":
    main()
