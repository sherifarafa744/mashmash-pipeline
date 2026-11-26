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
    elif cmd == "guard":
        wf = os.environ.get("WORKFLOW_FILE", "daily.yml")
        me = int(os.environ["GITHUB_RUN_ID"])
        want = target(dt.datetime.now(dt.timezone.utc))
        req = urllib.request.Request(
            f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/actions/workflows/{wf}/runs?status=completed&per_page=30",
            headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"]})
        runs = json.load(urllib.request.urlopen(req, timeout=60)).get("workflow_runs", [])
        for r in runs:
            if r["conclusion"] == "success" and r["id"] != me and parse(r["created_at"]) >= parse(SINCE) and target(parse(r["created_at"])) == want:
                print("skip")
                return
        print("run")

if __name__ == "__main__":
    main()
