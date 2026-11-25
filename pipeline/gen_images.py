"""Scene art via Cloudflare Workers AI flux-1-schnell (free 10k neurons/day).

Cost: ~173 neurons per 1024x1024 4-step image -> ~55 images/day free.
Model license: Apache 2.0 (commercial use OK). Commercial use of the free
allocation is allowed under Cloudflare's Self-Serve Subscription Agreement.
Character consistency: every prompt carries the same CHARACTER+STYLE block
(flux-1-schnell on Workers AI is text-only; no reference input).
"""
import base64, json, os, pathlib, sys, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from character import image_prompt

ACCOUNT = os.environ["CF_ACCOUNT_ID"]
TOKEN = os.environ["CF_API_TOKEN"]
ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> None:
    ep = json.loads((ROOT / "episode.json").read_text())
    (ROOT / "scenes").mkdir(exist_ok=True)
    for i, scene in enumerate(ep["scenes"], 1):
        body = json.dumps({"prompt": image_prompt(scene["image_prompt"]),
                           "steps": 4}).encode()
        req = urllib.request.Request(
            f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/@cf/black-forest-labs/flux-1-schnell",
            data=body, headers={"Authorization": f"Bearer {TOKEN}",
                                "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            out = json.load(r)
        (ROOT / "scenes" / f"scene{i}.png").write_bytes(
            base64.b64decode(out["result"]["image"]))
        print("scene", i, "ok")


if __name__ == "__main__":
    sys.exit(main())
