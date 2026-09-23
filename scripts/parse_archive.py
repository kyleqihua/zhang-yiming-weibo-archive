from pathlib import Path
from datetime import datetime
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_SRC = ROOT / "data/source/extracted_layout.txt"
LEGACY_SRC = ROOT / "data/source/extracted.txt"
SRC = LAYOUT_SRC if LAYOUT_SRC.exists() else LEGACY_SRC
OUT = ROOT / "data/posts.json"
META = ROOT / "data/meta.json"
EXTRACTION_META = ROOT / "data/source/extraction_meta.json"

raw = SRC.read_text(encoding="utf-8", errors="ignore")

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
    r"(?P<day>\d{1,2})\s*(?P<hour>\d{2})\s*:\s*(?P<minute>\d{2})"
)
matches = list(header.finditer(text))

source_specs = [
    ("微博浏览器插件", "微博浏览器插件"),
    ("我爱我家微群", "我爱我家微群"),
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

CJK = r"\u3400-\u9fff"
CJK_PUNCT = r"，。！？：；、、“”‘’《》【】（）"

LONG_ARTICLE_OVERRIDES = {
    "2015-05-07T07:20:00+08:00": {
        "text": "张嘉佳微博文字很好但书没看过，所以把书和龙虾都加入到了wish list",
        "attachment": {
            "type": "article",
            "label": "网页文章",
            "title": "张嘉佳&唐宋：十年一觉龙虾梦",
            "excerpt": "十几年前，我还是一个文艺青年。严格来讲，应该是文学青年。文学在当时的年轻人中尚属主流艺术……",
            "url": "https://www.sohu.com/a/13609448_115494",
            "provenance": "内容镜像：搜狐，2015-05-04，文/蒋政文（笔名“唐宋”）",
        },
    },
    "2015-11-17T20:20:00+08:00": {
        "text": '周日在南开大学北京校友活动：11.15 南开发声，我做了一个演讲。在演讲的前几天，我犹豫是做一个客套的"母校演讲" ，还是讲讲真实经历和感受，最后选择了后者。从现场反馈效果不错，龚克校长还邀我回学校分...',
        "attachment": {
            "type": "article",
            "label": "长微博",
            "title": "意料之外的大学生活和创业心路",
            "excerpt": "周日在南开大学北京校友活动：11.15 南开发声，我做了一个演讲。在演讲的前几天，我犹豫是做一个客套的“母校演讲”，还是讲讲真实经历和感受……",
            "url": "http://t.cn/RUEKuEI",
            "provenance": "原微博短链接",
        },
    },
    "2015-08-25T21:01:00+08:00": {
        "text": "「给产品技术人才的建议：不降级不投机，和优秀的人做有挑战的事」这作文是我自己写的。。。有点吃力哈。。但是是真心话，供产品技术人才参考。",
        "attachment": {
            "type": "article",
            "label": "长微博",
            "title": "给产品技术人才的建议：不降级不投机，和优秀的人做有挑战的事",
            "excerpt": "最近有点郁闷，又有候选人把我拒绝了。其实拒和被拒经常发生，并不都导致郁闷，但，候选人以这些理由选择别家公司除外……",
            "url": "http://t.cn/RyvCZQQ",
            "provenance": "原微博短链接",
        },
    },
    "2014-05-22T21:43:00+08:00": {
        "attachment": {
            "type": "article",
            "label": "长微博",
            "title": "我的二次创业——Egret Html5游戏引擎",
            "excerpt": "今年春天因为种种原因，我下决心开始自己人生中的第二次创业。很多关心我的朋友来跟我聊……",
            "url": "",
            "provenance": "PDF 中展开的长文预览",
        },
    },
    "2010-09-15T23:51:00+08:00": {
        "attachment": {
            "type": "article",
            "label": "长微博",
            "title": "互联网/移动互联网小团队创业第二集",
            "excerpt": "上一集收到了非常多的好评和很好的反馈，谢谢。这个系列是针对小团队白手起家创业……",
            "url": "",
            "provenance": "PDF 中展开的长文预览",
        },
    },
}


def consume_compact_prefix(s: str, target: str):
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


def normalize_visual_spacing(s: str):
    lines = [line.strip() for line in s.splitlines() if line.strip()]
    s = " ".join(lines)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t\r\f\v]+", " ", s)

    cjkish = rf"[{CJK}{CJK_PUNCT}]"
    s = re.sub(rf"(?<={cjkish}) +(?={cjkish})", "", s)
    s = re.sub(r" +(?=[，。！？：；、）》】])", "", s)
    s = re.sub(r"(?<=[《【（]) +", "", s)

    s = re.sub(r"\bO +网页链接\b", "O网页链接", s)
    s = re.sub(r"@ +(?=[A-Za-z0-9_\-\u3400-\u9fff])", "@", s)
    s = re.sub(r"# +([^#]+?) +#", r"#\1#", s)

    s = re.sub(r"([.!?])(?=[A-Z])", r"\1 ", s)
    s = re.sub(r" +(?=[,.;:!?])", "", s)

    # Chinese prose normally does not put a space between a number and Han text.
    s = re.sub(rf"(?<=\d) +(?=[{CJK}])", "", s)
    s = re.sub(rf"(?<=[{CJK}]) +(?=\d)", "", s)

    # A few PDF runs encode no geometric word gap. Keep this list small and
    # auditable instead of guessing broadly.
    spacing_repairs = {
        "ofour": "of our",
        "anddemand": "and demand",
        "andprofessionalism": "and professionalism",
        "appESPApplolicious": "appESP Applolicious",
    }
    for bad, good in spacing_repairs.items():
        s = s.replace(bad, good)

    return re.sub(r" {2,}", " ", s).strip()


def split_long_article_preview(content: str, dt_iso: str):
    """
    The PDF compiler expanded some Sina long-article link previews directly
    after the microblog text, flattening two UI layers into one string. Keep
    the microblog body and article preview as separate fields.
    """
    override = LONG_ARTICLE_OVERRIDES.get(dt_iso)
    attachment = None

    if "°" in content:
        body, _expanded = content.split("°", 1)
        content = body.strip()
        if override and override.get("attachment"):
            attachment = dict(override["attachment"])

    if override:
        if override.get("text"):
            content = override["text"]
        if override.get("attachment"):
            attachment = dict(override["attachment"])

    return content.strip(), attachment


def clean_content(s: str):
    # Decode HTML entities leaked from rich-link previews, e.g. &amp; -> &.
    s = html.unescape(s)

    # Do NOT delete a leading number here. The old rule corrupted
    # "6岁的时候" into "岁的时候".
    s = re.sub(
        r"\s*添加微信\s*1?\s*领取\s*200\s*个互联网创业项目\s*",
        "",
        s,
    )
    return normalize_visual_spacing(s)


posts = []
for idx, m in enumerate(matches):
    end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
    segment = text[m.end():end]

    y, mo, d, h, mi = map(
        int,
        [
            m.group("year"),
            m.group("month"),
            m.group("day"),
            m.group("hour"),
            m.group("minute"),
        ],
    )

    try:
        dt = datetime(y, mo, d, h, mi)
    except ValueError:
        continue

    source, remainder = extract_source(segment)
    content = clean_content(remainder)
    dt_iso = dt.strftime("%Y-%m-%dT%H:%M:00+08:00")
    content, attachment = split_long_article_preview(content, dt_iso)
    if not content:
        content = "（该条微博正文在公开存档中未能恢复）"

    digest = hashlib.sha1(
        f"{dt.isoformat()}\n{content}".encode("utf-8")
    ).hexdigest()[:12]

    flags = []
    if "此微博已被作者删除" in content:
        flags.append("deleted")
    if (
        "已设置仅展示半年内微博" in content
        or "正文在公开存档中未能恢复" in content
    ):
        flags.append("unavailable")
    if (
        content.startswith("转发微博")
        or "//@" in content
        or content.startswith("//")
    ):
        flags.append("repost")

    posts.append(
        {
            "id": digest,
            "datetime": dt_iso,
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
            "year": y,
            "month": mo,
            "day": d,
            "source": source,
            "text": content,
            "attachment": attachment,
            "flags": flags,
            "archiveIndex": idx + 1,
        }
    )

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
    sources[p["source"] or "来源未识别"] = (
        sources.get(p["source"] or "来源未识别", 0) + 1
    )

OUT.write_text(
    json.dumps(posts, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)

META.write_text(
    json.dumps(
        {
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
            "sources": dict(
                sorted(sources.items(), key=lambda kv: (-kv[1], kv[0]))
            ),
            "removedThirdPartyFooters": (
                json.loads(EXTRACTION_META.read_text()).get("footerBlocksRemoved", 0)
                if EXTRACTION_META.exists()
                else removed_footers
            ),
            "duplicatePostKeys": duplicate_keys,
            "extraction": (
                "coordinate-aware PDF text extraction"
                if SRC == LAYOUT_SRC
                else "legacy plain PDF text extraction"
            ),
            "method": (
                "PDF glyph coordinates -> line reconstruction -> page-level "
                "third-party footer removal -> high-confidence 张一鸣+timestamp parsing"
            ),
            "caveat": (
                "公开整理本标题写作2286条；仅展示能从PDF文本层可靠识别为"
                "张一鸣本人时间头的记录。转发关系、原微博ID、图片与互动数并不完整。"
            ),
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print(
    json.dumps(
        {
            "source": str(SRC),
            "posts": len(posts),
            "range": {
                "newest": posts[0]["datetime"] if posts else None,
                "oldest": posts[-1]["datetime"] if posts else None,
            },
            "duplicate_keys": duplicate_keys,
        },
        ensure_ascii=False,
        indent=2,
    )
)
