"""Build the cross-post kit for the episode that was just uploaded.

Writes social/caption.txt (Egyptian Arabic caption + hashtags) and
social/meta.json next to the final mp4. The workflow then attaches
episode_final.mp4 + caption.txt to a GitHub Release so a browser-driving
agent can curl them. Never fails the run. No exact counts, no personal
details, no links (Instagram captions do not make links clickable).
"""
import json, pathlib, random, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "social"

HOOKS = [
    "استنى لآخر ثانية! 😱",
    "بسبوسة وقعت في مصيبة جديدة 🐱",
    "تفتكر هتعدي منها؟ 👀",
    "الحكاية دي مش هتنساها 🎬",
    "كل جزء بينتهي في أحلى لحظة! 🔥",
]
TAGS_BASE = ["#بسبوسة", "#حكايات_بسبوسة", "#قصص_قطط", "#قطط", "#حكايات",
             "#حكايات", "#ريلز", "#مصر"]
TAGS_EXTRA = ["#قطه_كيوت", "#كرتون", "#قصص_مصورة", "#تريند", "#شورتس", "#قصص_حيوانات"]

def build(ep: dict) -> str:
    rnd = random.Random(ep.get("title", ""))
    hook = rnd.choice(HOOKS)
    vote = ep.get("vote") or {}
    lines = [hook, ep.get("title", "").strip()]
    if ep.get("celebration"):
        lines.append("بسبوسة بتشكركم على حبكم! 🎉 تحبوا الحكاية الجاية تكون عن إيه؟ قولولنا في الكومنتات")
    else:
        lines.append(f"الجزء {ep.get('part', 1)} من حكايات بسبوسة")
        if ep.get("cliffhanger"):
            lines.append(ep["cliffhanger"].strip())
        if vote.get("question"):
            lines.append(f"{vote['question']} {vote.get('option_a', '')} ولا {vote.get('option_b', '')}؟ اكتبوا في الكومنتات 👇")
    lines.append("تابعونا عشان حكاية جديدة كل يوم 🐱 اليوتيوب: @HekayatBasbusa")
    tags = TAGS_BASE + rnd.sample(TAGS_EXTRA, 3)
    return "\n\n".join(l for l in lines if l) + "\n\n" + " ".join(tags) + "\n"

def main() -> None:
    try:
        ep = json.loads((ROOT / "episode.json").read_text())
        OUT.mkdir(exist_ok=True)
        (OUT / "caption.txt").write_text(build(ep), encoding="utf-8")
        (OUT / "meta.json").write_text(json.dumps({
            "title": ep.get("title"), "part": ep.get("part"),
            "celebration": bool(ep.get("celebration")),
            "built_at": datetime.datetime.utcnow().isoformat() + "Z"},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print("social kit written")
    except Exception as e:
        print("social kit failed (non-fatal):", e)

if __name__ == "__main__":
    main()
