#!/usr/bin/env python3
"""
ニュース定点観測 - GitHub Pages 静的ミラー生成スクリプト

data.json (categories + articles のスナップショット) を読み込み、
index.html を静的に書き出す。

このミラーはスナップショットであり、リアルタイムには更新されない。
最新のカテゴリ管理・自動収集は claude.ai 上のArtifact本体で行われ、
このリポジトリはClaudeに頼んで手動で同期する運用(便利帳プロジェクトと同じ方針)。

使い方:
    python3 generate.py
"""
import json
import html
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
DATA_PATH = HERE / "data.json"
OUT_PATH = HERE / "index.html"
ARTIFACT_URL = "https://claude.ai/code/artifact/77481c43-0519-4a44-8502-27c32be1c994"

PALETTE = ['#B23A48', '#1F7A5C', '#8A5A00', '#4B4E9E', '#0E7C86', '#B2621E',
           '#7A3E9D', '#2C6E49', '#9C4221', '#33608A']


def cat_color(cat_id: str) -> str:
    h = 0
    for ch in cat_id:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return PALETTE[h % len(PALETTE)]


def fmt_date(iso: str) -> str:
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso[:10]
    d_jst = d.astimezone(timezone.utc)
    return f"{d_jst.month}/{d_jst.day}"


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def build():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    categories = sorted(data["categories"], key=lambda c: c.get("order", 0))
    articles = data["articles"]
    synced_at = data.get("syncedAt", "")

    cat_by_id = {c["id"]: c for c in categories}
    articles = [a for a in articles if a["categoryId"] in cat_by_id]
    articles.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)

    cards_html = []
    for a in articles:
        c = cat_by_id[a["categoryId"]]
        color = cat_color(a["categoryId"])
        cards_html.append(f'''
      <a class="card" href="{esc(a.get("url", "#"))}" target="_blank" rel="noopener noreferrer" data-cat="{esc(a["categoryId"])}">
        <div class="card-meta"><span class="dot" style="background:{color}"></span>
          <span class="cat-name">{esc(c["name"])}</span>
          <span class="sep">・</span><span>{esc(a.get("source", ""))}</span>
          <time>{esc(fmt_date(a.get("publishedAt", "")))}</time></div>
        <h3>{esc(a.get("title", "(無題)"))}</h3>
        <p>{esc(a.get("summary", ""))}</p>
      </a>''')

    tabs_html = ['<div class="tab active" data-cat="all">全分野</div>']
    for c in categories:
        color = cat_color(c["id"])
        tabs_html.append(
            f'<div class="tab" data-cat="{esc(c["id"])}"><span class="dot" style="background:{color}"></span>{esc(c["name"])}</div>'
        )

    try:
        synced_display = datetime.fromisoformat(synced_at.replace("Z", "+00:00")).strftime("%Y年%m月%d日 %H:%M UTC")
    except ValueError:
        synced_display = synced_at

    html_out = f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ニュース定点観測</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@400;700;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=JetBrains+Mono:wght@400;500;700&display=swap">
<style>
  :root {{
    --bg:#f4f5f7; --surface:#fff; --border:#d8dbe2; --text:#14181f; --text-muted:#5b6270;
    --accent:#2453c2; --accent-soft:#e4ebfc; --shadow:0 1px 2px rgba(20,24,31,.04),0 8px 24px -12px rgba(20,24,31,.12);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg:#10131a; --surface:#171b24; --border:#2b3140; --text:#e7e9ee; --text-muted:#9aa1b0;
      --accent:#6e93f2; --accent-soft:#22304f; --shadow:0 1px 2px rgba(0,0,0,.3),0 12px 28px -14px rgba(0,0,0,.55);
    }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font-family:"Zen Kaku Gothic New","Hiragino Sans","Noto Sans JP",sans-serif; -webkit-font-smoothing:antialiased; }}
  .app {{ max-width:1080px; margin:0 auto; padding:20px 20px 64px; }}
  .masthead {{ border-bottom:3px solid var(--text); padding-bottom:14px; margin-bottom:10px; }}
  .site-title {{ font-family:"Shippori Mincho B1",serif; font-weight:800; font-size:clamp(26px,4vw,34px); letter-spacing:.04em; margin:0; }}
  .site-sub {{ font-size:12px; color:var(--text-muted); margin-top:2px; }}
  .sync-note {{ font-size:11.5px; color:var(--text-muted); background:var(--accent-soft); border:1px solid var(--border); border-radius:8px; padding:8px 12px; margin:14px 0; }}
  .sync-note a {{ color:var(--accent); font-weight:700; }}
  .cat-tabs {{ display:flex; gap:6px; overflow-x:auto; padding:14px 0; }}
  .tab {{ flex:none; display:flex; align-items:center; gap:6px; background:var(--surface); border:1px solid var(--border); color:var(--text-muted); padding:7px 13px; border-radius:999px; font-size:13px; font-weight:500; cursor:pointer; white-space:nowrap; }}
  .tab .dot {{ width:7px; height:7px; border-radius:50%; }}
  .tab.active {{ background:var(--text); border-color:var(--text); color:var(--bg); }}
  .feed {{ display:grid; grid-template-columns:repeat(2,1fr); gap:14px; }}
  @media (max-width:680px) {{ .feed {{ grid-template-columns:1fr; }} }}
  .card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px; box-shadow:var(--shadow); display:flex; flex-direction:column; gap:8px; text-decoration:none; color:var(--text); }}
  .card:hover {{ border-color:var(--accent); }}
  .card-meta {{ display:flex; align-items:center; gap:8px; font-size:11.5px; color:var(--text-muted); }}
  .card-meta .dot {{ width:7px; height:7px; border-radius:50%; }}
  .card-meta .cat-name {{ font-weight:700; }}
  .card-meta time {{ font-family:"JetBrains Mono",monospace; margin-left:auto; }}
  .card h3 {{ margin:0; font-size:16px; line-height:1.45; font-weight:700; text-wrap:balance; }}
  .card p {{ margin:0; font-size:13px; line-height:1.6; color:var(--text-muted); }}
  footer {{ margin-top:34px; padding-top:16px; border-top:1px solid var(--border); font-size:11.5px; color:var(--text-muted); }}
  [hidden] {{ display:none !important; }}
</style>
</head>
<body>
<div class="app">
  <header class="masthead">
    <h1 class="site-title">ニュース定点観測</h1>
    <div class="site-sub">自分で選んだ分野だけを、毎朝自動で集める個人ニュースボード(静的ミラー)</div>
  </header>
  <div class="sync-note">これは <strong>{esc(synced_display)}</strong> 時点のスナップショットです。分野の追加・削除やリアルタイム更新は <a href="{esc(ARTIFACT_URL)}" target="_blank" rel="noopener">claude.ai の本体ページ</a> で行われ、このページはClaudeに依頼したときに手動で同期されます。</div>
  <div class="cat-tabs" id="tabs">{"".join(tabs_html)}</div>
  <main class="feed" id="feed">{"".join(cards_html)}</main>
  <footer>ニュース定点観測 ・ 静的ミラー ・ matsushima-ui/news-desk</footer>
</div>
<script>
(function () {{
  var tabs = document.getElementById('tabs');
  var cards = document.querySelectorAll('.card');
  tabs.addEventListener('click', function (e) {{
    var tab = e.target.closest('.tab');
    if (!tab) return;
    Array.prototype.forEach.call(tabs.querySelectorAll('.tab'), function (t) {{ t.classList.remove('active'); }});
    tab.classList.add('active');
    var cat = tab.getAttribute('data-cat');
    cards.forEach(function (c) {{
      c.hidden = (cat !== 'all' && c.getAttribute('data-cat') !== cat);
    }});
  }});
}})();
</script>
</body>
</html>
'''
    OUT_PATH.write_text(html_out, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(articles)} articles, {len(categories)} categories)")


if __name__ == "__main__":
    build()
