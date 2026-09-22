from pathlib import Path
from datetime import datetime
import hashlib, json, re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/source/extracted.txt"
OUT = ROOT / "data/posts.json"
META = ROOT / "data/meta.json"

raw = SRC.read_text(encoding="utf-8", errors="ignore")

# The circulating PDF has a third-party watermark/footer inserted on most pages.
# Remove only the recurring footer pattern, not ordinary post text.
footer_patterns = [
    r"\n\d{1,3}\n添加微信1领取\n200\n个互联网创业项目\n\n",
    r"\n\d{1,3}\n添加微信领取\n200\n个互联网创业项目\n\n",
    r"\n\d{1,3}\n添加微信1?领取\n200\n个互联网创业项目\s*$",
]
text = raw
removed_footers = 0
for pat in footer_patterns:
    text, n = re.subn(pat, "\n", text)
    removed_footers += n

header = re.compile(
    r"张\s*一\s*鸣\s*"
    r"(?P<year>20\d{2})\s*-\s*(?P<month>\d{1,2})\s*-\s*"
    r"(?P<day>\d{1,2})(?P<hour>\d{2})\s*:\s*(?P<minute>\d{2})"
)
matches = list(header.finditer(text))

source_specs = [
    ("微博浏览器插件", "微博浏览器插件"),
    ("微活动-IT龙门阵...", "微活动-IT龙门阵"),
    ("外滩画报daily", "外滩画报 daily"),
    ("手机优酷", "手机优酷"),
    ("秒拍客户端", "秒拍客户端"),
    ("起床大作战", "起床大作战"),
    ("分享按钮", "分享按钮"),
    ("优酷土豆", "优酷土豆"),
    ("蚂蚁书摘", "蚂蚁书摘"),
    ("新浪博客", "新浪博客"),
    ("微博搜索", "微博搜索"),
    ("豆瓣音乐", "豆瓣音乐"),
    ("豆瓣web", "豆瓣 web"),
    ("知乎网", "知乎网"),
    ("bshare", "bShare"),
    ("App汇", "App汇"),
    ("手机微博触屏版", "手机微博触屏版"),
    ("搜狗高速浏览器", "搜狗高速浏览器"),
    ("Android客户端", "Android 客户端"),
    ("iPhone6Plus", "iPhone 6 Plus"),
    ("iPhone6s", "iPhone 6s"),
    ("iPhone6", "iPhone 6"),
    ("iPhone客户端", "iPhone 客户端"),
    ("iPad客户端", "iPad 客户端"),
    ("S60客户端", "S60 客户端"),
    ("专业版微博", "专业版微博"),
    ("微博weibo.com", "微博 weibo.com"),
    ("微博手机版", "微博手机版"),
    ("今日头条", "今日头条"),
    ("豆瓣电影", "豆瓣电影"),
    ("微公益", "微公益"),
    ("房产资讯", "房产资讯"),
    ("iPhone", "iPhone"),
]
source_specs.sort(key=lambda x: len(x[0]), reverse=True)

def consume_compact_prefix(s: str, target: str):
    """Consume target from s while ignoring whitespace between target chars."""
    i = 0
    j = 0
    while i < len(s) and j < len(target):
        if s[i].isspace():
            i += 1
            continue
        if s[i] != target[j]:
            return None
        i += 1
        j += 1
    if j != len(target):
        return None
    return s[i:]

def extract_source(segment: str):
    s = segment.lstrip()
    if not s.startswith("来自"):
        return "", s
    for compact, display in source_specs:
        rest = consume_compact_prefix(s, "来自" + compact)
        if rest is not None:
            return display, rest.lstrip()
    return "", s

def clean_content(s: str):
    # A page number can land at the beginning of a post after PDF pagination.
    s = re.sub(r"^\s*\d{1,3}\s*\n(?=\S)", "", s, count=1)
    s = re.sub(r"\n\d{1,3}\s*$", "", s)
    # Remove any residual third-party promo watermark if line extraction changed.
    s = re.sub(r"\s*添加微信\s*1?\s*领取\s*200\s*个互联网创业项目\s*", "", s)
    # Normalize PDF line-wraps into the single-flow style of a Weibo post.
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r"\s*\n\s*", "", s)
    s = re.sub(r" {2,}", " ", s)
    return s.strip()

posts = []
for idx, m in enumerate(matches):
    end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
    segment = text[m.end():end]

    y, mo, d, h, mi = map(int, [
        m.group("year"), m.group("month"), m.group("day"),
        m.group("hour"), m.group("minute")
    ])
    try:
        dt = datetime(y, mo, d, h, mi)
    except ValueError:
        continue

    source, remainder = extract_source(segment)
    content = clean_content(remainder)
    if not content:
        content = "（该条微博正文在公开存档中未能恢复）"

    digest = hashlib.sha1(
        f"{dt.isoformat()}\n{content}".encode("utf-8")
    ).hexdigest()[:12]

    flags = []
    if "此微博已被作者删除" in content:
        flags.append("deleted")
    if "已设置仅展示半年内微博" in content or "正文在公开存档中未能恢复" in content:
        flags.append("unavailable")
    if content.startswith("转发微博") or "//@" in content or content.startswith("//"):
        flags.append("repost")

    posts.append({
        "id": digest,
        "datetime": dt.strftime("%Y-%m-%dT%H:%M:00+08:00"),
        "date": dt.strftime("%Y-%m-%d"),
        "time": dt.strftime("%H:%M"),
        "year": y,
        "month": mo,
        "day": d,
        "source": source,
        "text": content,
        "flags": flags,
        "archiveIndex": idx + 1,
    })

# Keep the source ordering (newest -> oldest), but report duplicate timestamps separately.
seen = set()
duplicate_keys = 0
for p in posts:
    key = (p["datetime"], p["text"])
    if key in seen:
        duplicate_keys += 1
    seen.add(key)

years = {}
sources = {}
for p in posts:
    years[str(p["year"])] = years.get(str(p["year"]), 0) + 1
    sources[p["source"] or "来源未识别"] = sources.get(p["source"] or "来源未识别", 0) + 1

OUT.write_text(json.dumps(posts, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
META.write_text(json.dumps({
    "project": "张一鸣微博档案（非官方复原）",
    "sourceTitle": "张一鸣微博日记 2286 条",
    "sourceCompiler": "方建勇",
    "sourceCompiledDate": "2019-05-25",
    "sourceFileAlias": "张一鸣微博2886条.pdf",
    "parsedPosts": len(posts),
    "dateRange": {
        "newest": posts[0]["datetime"] if posts else None,
        "oldest": posts[-1]["datetime"] if posts else None,
    },
    "years": years,
    "sources": dict(sorted(sources.items(), key=lambda kv: (-kv[1], kv[0]))),
    "removedThirdPartyFooters": removed_footers,
    "duplicatePostKeys": duplicate_keys,
    "method": "PDF text layer -> recurring footer removal -> high-confidence 张一鸣+timestamp header parsing",
    "caveat": "公开整理本标题写作2286条；仅展示能从PDF文本层可靠识别为张一鸣本人时间头的记录。转发关系、原微博ID、图片与互动数并不完整。",
}, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(json.loads(META.read_text()), ensure_ascii=False, indent=2))
print("\nSAMPLES")
for p in posts[:3] + posts[-3:]:
    print(p["datetime"], p["source"], p["text"][:140])
