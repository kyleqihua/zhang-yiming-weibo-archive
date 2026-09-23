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

article = at("2015-08-25T21:01")
assert len(article) == 1
assert article[0]["text"] == "「给产品技术人才的建议：不降级不投机，和优秀的人做有挑战的事」这作文是我自己写的。。。有点吃力哈。。但是是真心话，供产品技术人才参考。"
assert article[0]["attachment"]["title"] == "给产品技术人才的建议：不降级不投机，和优秀的人做有挑战的事"
assert article[0]["attachment"]["url"] == "http://t.cn/RyvCZQQ"
assert "最近有点郁闷" not in article[0]["text"]

speech = at("2015-11-17T20:20")
assert len(speech) == 1
assert speech[0]["attachment"]["title"] == "意料之外的大学生活和创业心路"
assert "意料之外的大学生活和创业心路意料之外" not in speech[0]["text"]

lobster = at("2015-05-07T07:20")
assert len(lobster) == 1
assert lobster[0]["text"] == "张嘉佳微博文字很好但书没看过，所以把书和龙虾都加入到了wish list"
assert lobster[0]["attachment"]["title"] == "张嘉佳&唐宋：十年一觉龙虾梦"
assert "十几年前，我还是一个文艺青年" not in lobster[0]["text"]
assert "&amp;" not in lobster[0]["text"]
assert lobster[0]["attachment"]["url"].startswith("https://www.sohu.com/")

gates = at("2015-09-24T09:59")
assert len(gates) == 1
assert gates[0]["text"].startswith("没敢问手机等产品问题"), gates[0]["text"]

textbook = at("2015-08-23T00:42")
assert len(textbook) == 1
assert textbook[0]["text"].startswith("其实知识含量最大的书是教科书"), textbook[0]["text"]

consumption = [p for p in posts if "关于消费" in p["text"]]
assert len(consumption) >= 2

bad_long_runs = []
for p in posts:
    for token in re.findall(r"[A-Za-z]{30,}", p["text"]):
        bad_long_runs.append((p["datetime"], token))
assert not bad_long_runs, bad_long_runs[:20]

assert meta["removedThirdPartyFooters"] >= 300
assert meta["extraction"] == "coordinate-aware PDF text extraction"

html_entity_re = re.compile(r"&(?:amp|quot|apos|lt|gt|nbsp|#\d+|#x[0-9a-fA-F]+);")
entity_hits = [
    (p["datetime"], p["text"])
    for p in posts
    if html_entity_re.search(p["text"])
]
assert not entity_hits, entity_hits[:10]

print(json.dumps({
    "status": "ok",
    "posts": len(posts),
    "train_post": train[0]["text"],
    "english_sample": english[0]["text"],
    "footer_blocks_removed": meta["removedThirdPartyFooters"],
}, ensure_ascii=False, indent=2))
