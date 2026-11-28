"""Scene art via Cloudflare Workers AI flux-1-schnell (free 10k neurons/day).

Cost: ~173 neurons per 1024x1024 4-step image -> ~55 images/day free.
Model license: Apache 2.0 (commercial use OK). Commercial use of the free
allocation is allowed under Cloudflare's Self-Serve Subscription Agreement.
Character consistency: every prompt carries the same CHARACTER+STYLE block
(flux-1-schnell on Workers AI is text-only; no reference input).
"""
import base64, json, os, pathlib, sys, urllib.error, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from character import image_prompt

ACCOUNT = os.environ["CF_ACCOUNT_ID"]
TOKEN = os.environ["CF_API_TOKEN"]
ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> None:
    ep = json.loads((ROOT / "episode.json").read_text())
    (ROOT / "scenes").mkdir(exist_ok=True)
    for old in (ROOT / "scenes").glob("scene*.png"):  # never reuse a stale image from an earlier build
        old.unlink()
    for i, scene in enumerate(ep["scenes"], 1):
        body = json.dumps({"prompt": image_prompt(scene["image_prompt"]),
                           "steps": 4}).encode()
        req = urllib.request.Request(
            f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/@cf/black-forest-labs/flux-1-schnell",
            data=body, headers={"Authorization": f"Bearer {TOKEN}",
                                "Content-Type": "application/json"})
        out = None
        import time
        for attempt in range(8):  # 429 = rate/quota: log the body, wait and retry (up to ~25 min per image)
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    out = json.load(r)
                break
            except urllib.error.HTTPError as e:
                print(f"scene {i} attempt {attempt + 1}: HTTP {e.code} {e.read().decode()[:300]}", flush=True)
                if e.code not in (429, 500, 502, 503, 504):
                    raise
                time.sleep(min(60 * (attempt + 1), 300))
        if out is None:
            raise SystemExit(f"image generation kept failing for scene {i}")
        (ROOT / "scenes" / f"scene{i}.png").write_bytes(
            base64.b64decode(out["result"]["image"]))
        print("scene", i, "ok")


if __name__ == "__main__":
    sys.exit(main())
