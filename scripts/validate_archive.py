from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
posts = json.loads((ROOT / "data/posts.json").read_text())
meta = json.loads((ROOT / "data/meta.json").read_text())

assert len(posts) == meta["parsedPosts"]
assert len(posts) >= 2164, len(posts)

def at(dt):
    return [p for p in posts if p["datetime"].startswith(dt)]

train = at("2015-04-30T22:01")
assert len(train) == 1
assert train[0]["text"].startswith("6岁的时候，第一坐火车。"), train[0]["text"]

english = at("2015-04-29T20:24")
assert len(english) == 2
joined = "\n".join(p["text"] for p in english)
assert "In other words, we attempt to defend our cosciousness against reality, thereby limiting our awareness." in joined
assert "Many aspects of the reality of the world and of our relationship to the world are painful to us." in joined
assert "ofour" not in joined

develop = at("2015-11-07T12:07")
assert len(develop) == 1
assert develop[0]["text"] == "Develop a company as a product."

consumption = [p for p in posts if "关于消费" in p["text"]]
assert len(consumption) >= 2

bad_long_runs = []
for p in posts:
    for token in re.findall(r"[A-Za-z]{30,}", p["text"]):
        bad_long_runs.append((p["datetime"], token))
assert not bad_long_runs, bad_long_runs[:20]

assert meta["removedThirdPartyFooters"] >= 300
assert meta["extraction"] == "coordinate-aware PDF text extraction"

print(json.dumps({
    "status": "ok",
    "posts": len(posts),
    "train_post": train[0]["text"],
    "english_sample": english[0]["text"],
    "footer_blocks_removed": meta["removedThirdPartyFooters"],
}, ensure_ascii=False, indent=2))
