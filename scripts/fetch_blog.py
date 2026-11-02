"""네이버 블로그 RSS를 읽어 홈페이지의 '블로그 최신 글' 영역을 갱신한다.
GitHub Actions에서 매일 실행된다. 표준 라이브러리만 사용."""
import html, re, sys, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

RSS = "https://rss.blog.naver.com/big_tree_clinic.xml"
TARGETS = {"index.html": 4, "column/index.html": 12}

def fetch():
    req = urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0 (bigtree-ent site updater)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def clean(t, n=90):
    t = re.sub(r"<[^>]+>", " ", html.unescape(t or ""))
    t = re.sub(r"#\S+", " ", t)                      # 해시태그 제거
    t = re.sub(r"\s+", " ", t).strip()
    return (t[:n].rstrip() + "…") if len(t) > n else t

def items(raw):
    root = ET.fromstring(raw)
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip().split("?")[0]
        if not title or not link:
            continue
        try:
            d = parsedate_to_datetime(it.findtext("pubDate"))
            date = d.strftime("%Y.%m.%d"); iso = d.strftime("%Y-%m-%d")
        except Exception:
            date = iso = ""
        out.append(dict(title=title, link=link, date=date, iso=iso,
                        cat=(it.findtext("category") or "").strip(), desc=clean(it.findtext("description"))))
    return out

def render(posts, n):
    li = "\n".join(
        f'        <li><a href="{html.escape(p["link"])}" target="_blank" rel="noopener">'
        f'<span class="meta"><time datetime="{p["iso"]}">{p["date"]}</time> · 네이버 블로그</span>'
        f'<span class="hl">{html.escape(p["title"], quote=False)}</span>'
        + (f'<span class="dek">{html.escape(p["desc"], quote=False)}</span>' if p["desc"] else "")
        + "</a></li>" for p in posts[:n])
    return f'<!--BLOG:START-->\n      <ul class="blog-list">\n{li}\n      </ul>\n      <!--BLOG:END-->'

def main():
    posts = items(fetch())
    if not posts:
        print("no posts"); return 0
    changed = False
    for path, n in TARGETS.items():
        s = open(path, encoding="utf-8").read()
        s2 = re.sub(r"<!--BLOG:START-->.*?<!--BLOG:END-->", lambda m: render(posts, n), s, flags=re.S)
        if s2 != s:
            open(path, "w", encoding="utf-8").write(s2); changed = True
    print("updated" if changed else "no change", len(posts))
    return 0

if __name__ == "__main__":
    sys.exit(main())
