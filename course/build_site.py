#!/usr/bin/env python3
"""把本目录的课程 Markdown 构建成静态站点（GitHub Pages 用）。

用法: python3 build_site.py --out dist
依赖: pip install markdown
"""
import argparse
import re
import shutil
from pathlib import Path

import markdown

COURSE_DIR = Path(__file__).resolve().parent

CHAPTERS = [
    ("README", "课程首页"),
    ("01-overview", "01 · 快速上手与总览"),
    ("02-gamepad", "02 · 手柄状态监控"),
    ("03-calibration", "03 · 标定中心"),
    ("04-dual-arm", "04 · 双臂操控"),
    ("05-navigation", "05 · 建图导航"),
    ("06-workflow", "06 · 工作流编排"),
    ("07-api", "07 · HTTP API 速查"),
    ("08-topics", "08 · ROS 话题速查"),
]

TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · XR-AIH1 使用教程</title>
<style>
  :root {{
    --bg: #f6f7fb; --card: #ffffff; --text: #1f2430; --muted: #6b7280;
    --accent: #6d4df6; --border: #e5e7eb; --code-bg: #121023; --code-text: #e6e1ff;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; display: flex; min-height: 100vh;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", -apple-system, sans-serif;
    background: var(--bg); color: var(--text);
  }}
  nav {{
    width: 240px; flex-shrink: 0; padding: 24px 16px; position: sticky; top: 0;
    height: 100vh; overflow-y: auto; background: var(--card); border-right: 1px solid var(--border);
  }}
  nav .brand {{ font-weight: 700; font-size: 15px; margin-bottom: 4px; }}
  nav .sub {{ font-size: 12px; color: var(--muted); margin-bottom: 18px; }}
  nav a {{
    display: block; padding: 8px 12px; margin: 2px 0; border-radius: 8px;
    color: var(--text); text-decoration: none; font-size: 14px;
  }}
  nav a:hover {{ background: #eef0ff; }}
  nav a.active {{ background: var(--accent); color: #fff; }}
  main {{ flex: 1; min-width: 0; padding: 32px 40px 80px; }}
  .content {{ max-width: 860px; margin: 0 auto; background: var(--card);
    border: 1px solid var(--border); border-radius: 14px; padding: 40px 48px; }}
  h1 {{ font-size: 26px; border-bottom: 2px solid var(--accent); padding-bottom: 10px; }}
  h2 {{ font-size: 20px; margin-top: 36px; }}
  h3 {{ font-size: 16px; }}
  blockquote {{
    margin: 16px 0; padding: 12px 18px; background: #f3f0ff;
    border-left: 4px solid var(--accent); border-radius: 0 8px 8px 0; color: #4c4a63;
  }}
  blockquote p {{ margin: 4px 0; }}
  code {{
    font-family: "JetBrains Mono", Consolas, monospace; font-size: 0.9em;
    background: #efeefb; padding: 2px 6px; border-radius: 5px; color: #4c3fd6;
  }}
  pre {{ background: var(--code-bg); color: var(--code-text); padding: 16px 18px;
    border-radius: 10px; overflow-x: auto; line-height: 1.55; }}
  pre code {{ background: none; color: inherit; padding: 0; font-size: 13px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
  th, td {{ border: 1px solid var(--border); padding: 8px 12px; text-align: left; }}
  th {{ background: #f3f4f6; }}
  img {{ max-width: 100%; border: 1px solid var(--border); border-radius: 10px;
    display: block; margin: 20px auto 6px; }}
  p > em:only-child {{ text-align: center; color: var(--muted); font-size: 13px; }}
  a {{ color: var(--accent); }}
  hr {{ border: none; border-top: 1px solid var(--border); margin: 32px 0; }}
  li {{ margin: 4px 0; }}
</style>
</head>
<body>
<nav>
  <div class="brand">XR-AIH1 使用教程</div>
  <div class="sub">XR-H1 双臂升降整机 · 客户手册</div>
  {nav}
</nav>
<main><div class="content">
{body}
</div></main>
</body>
</html>"""


def build(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if (COURSE_DIR / "screenshots").is_dir():
        shutil.copytree(COURSE_DIR / "screenshots", out_dir / "screenshots", dirs_exist_ok=True)

    for slug, label in CHAPTERS:
        src = COURSE_DIR / f"{slug}.md"
        if not src.is_file():
            raise SystemExit(f"missing chapter file: {src}")
        text = src.read_text(encoding="utf-8")
        body = markdown.markdown(text, extensions=["tables", "fenced_code"])
        # 章节间互链 xxx.md -> xxx.html（静态站没有 .md 路由）
        body = re.sub(r'href="([^"]+)\.md"', r'href="\1.html"', body)
        title_match = re.search(r"<h1>(.*?)</h1>", body)
        title = re.sub(r"<[^>]+>", "", title_match.group(1)) if title_match else slug
        nav = []
        for nav_slug, nav_label in CHAPTERS:
            active = ' class="active"' if nav_slug == slug else ""
            nav.append(f'<a href="{nav_slug}.html"{active}>{nav_label}</a>')
        html = TEMPLATE.format(title=title, nav="\n".join(nav), body=body)
        (out_dir / f"{slug}.html").write_text(html, encoding="utf-8")

    shutil.copyfile(out_dir / "README.html", out_dir / "index.html")
    print(f"built {len(CHAPTERS)} pages -> {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="dist")
    args = parser.parse_args()
    build(Path(args.out).resolve())
