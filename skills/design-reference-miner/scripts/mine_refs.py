#!/usr/bin/env python3
"""Mine public web design references into a persistent local library."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright

SITES = [
    ("awwwards_home", "https://www.awwwards.com/"),
    ("dribbble", "https://dribbble.com/"),
    ("shadergradient", "https://shadergradient.co/"),
    ("dark_design", "https://www.dark.design/"),
    ("moncy", "https://www.moncy.dev/"),
    ("naresh_khatri", "https://www.nareshkhatri.site/#projects"),
    ("portfolio_3d", "https://3d-portfolio-website-gamma.vercel.app/"),
    ("durves", "https://www.durves.com/"),
    ("calltoinspiration", "https://calltoinspiration.com/"),
    ("omma_build", "https://omma.build/"),
]

EXTRACT_JS = r"""
() => {
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const result = {
    title: document.title,
    url: location.href,
    colors: {}, fonts: {}, headings: [], buttons: [], sections: [],
    links: [], assets: { css: [], js: [], images: [], fonts: [] },
    metrics: { elements: document.querySelectorAll('*').length }
  };
  const bump = (obj, key) => { if (key) obj[key] = (obj[key] || 0) + 1; };
  let count = 0;
  for (const el of document.querySelectorAll('*')) {
    if (++count > 2200) break;
    const cs = getComputedStyle(el);
    const bg = cs.backgroundColor;
    const fg = cs.color;
    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') bump(result.colors, bg);
    if (fg) bump(result.colors, fg);
    if (cs.fontFamily) bump(result.fonts, cs.fontFamily.split(',')[0].replace(/["']/g, ''));
  }
  document.querySelectorAll('h1,h2,h3').forEach((h) => {
    if (result.headings.length >= 16) return;
    const cs = getComputedStyle(h);
    result.headings.push({ tag: h.tagName, text: clean(h.innerText).slice(0, 180), size: cs.fontSize, weight: cs.fontWeight, family: cs.fontFamily.split(',')[0], color: cs.color, lineHeight: cs.lineHeight });
  });
  document.querySelectorAll('button,a,[role=button]').forEach((b) => {
    if (result.buttons.length >= 24) return;
    const text = clean(b.innerText || b.getAttribute('aria-label') || b.getAttribute('title'));
    if (!text && b.tagName !== 'BUTTON') return;
    const cs = getComputedStyle(b);
    result.buttons.push({ text: text.slice(0, 90), tag: b.tagName, href: b.href || null, bg: cs.backgroundColor, fg: cs.color, radius: cs.borderRadius, padding: cs.padding, border: cs.border });
  });
  document.querySelectorAll('section,main,header,footer,[class*="hero"],[class*="project"],[class*="card"]').forEach((s) => {
    if (result.sections.length >= 30) return;
    const cs = getComputedStyle(s);
    const rect = s.getBoundingClientRect();
    result.sections.push({ tag: s.tagName, className: s.className?.toString().slice(0, 120) || '', text: clean(s.innerText).slice(0, 180), display: cs.display, position: cs.position, bg: cs.backgroundColor, radius: cs.borderRadius, width: Math.round(rect.width), height: Math.round(rect.height) });
  });
  document.querySelectorAll('a[href]').forEach((a) => {
    if (result.links.length >= 120) return;
    result.links.push({ text: clean(a.innerText || a.getAttribute('aria-label')).slice(0, 90), href: a.href });
  });
  document.querySelectorAll('link[rel="stylesheet"]').forEach((l) => result.assets.css.push(l.href));
  document.querySelectorAll('script[src]').forEach((s) => result.assets.js.push(s.src));
  document.querySelectorAll('img[src], source[srcset]').forEach((img) => {
    const src = img.currentSrc || img.src || (img.srcset || '').split(' ')[0];
    if (src && result.assets.images.length < 160) result.assets.images.push(src);
  });
  document.querySelectorAll('link[href]').forEach((l) => {
    const href = l.href || '';
    if (/font|woff|ttf|otf/i.test(href)) result.assets.fonts.push(href);
  });
  result.colors = Object.fromEntries(Object.entries(result.colors).sort((a,b)=>b[1]-a[1]).slice(0,24));
  result.fonts = Object.fromEntries(Object.entries(result.fonts).sort((a,b)=>b[1]-a[1]).slice(0,12));
  result.assets.css = [...new Set(result.assets.css)].slice(0,60);
  result.assets.js = [...new Set(result.assets.js)].slice(0,80);
  result.assets.images = [...new Set(result.assets.images)].slice(0,160);
  result.assets.fonts = [...new Set(result.assets.fonts)].slice(0,30);
  return result;
}
"""


def safe_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", name).strip("-")[:120] or "asset"


def fetch_text(url: str, timeout: int = 20) -> str | None:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 DesignReferenceMiner/1.0"})
        with urlopen(req, timeout=timeout) as response:
            raw = response.read(1_800_000)
            return raw.decode("utf-8", errors="ignore")
    except Exception:
        return None


def same_or_public(base_url: str, asset_url: str) -> bool:
    base = urlparse(base_url)
    asset = urlparse(asset_url)
    return asset.scheme in {"http", "https"} and (asset.netloc == base.netloc or asset_url.endswith(".css"))


def scrape_site(page, name: str, url: str, out_root: Path) -> dict:
    out_dir = out_root / name
    out_dir.mkdir(parents=True, exist_ok=True)
    info = {"name": name, "url": url, "ok": False, "errors": []}
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=55_000)
        try:
            page.wait_for_load_state("networkidle", timeout=12_000)
        except Exception:
            pass
        for y in (320, 900, 1800, 3200):
            page.evaluate(f"window.scrollTo(0, {y})")
            time.sleep(0.35)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.8)
        info["title"] = page.title()
        info["final_url"] = page.url
        page.screenshot(path=str(out_dir / "desktop.png"), full_page=False)
        html = page.content()
        (out_dir / "page.html").write_text(html, encoding="utf-8")
        extract = page.evaluate(EXTRACT_JS)
        (out_dir / "extract.json").write_text(json.dumps(extract, ensure_ascii=False, indent=2), encoding="utf-8")
        assets = extract.get("assets", {})
        asset_lines = []
        for kind, values in assets.items():
            asset_lines.append(f"## {kind}")
            asset_lines.extend(values)
            asset_lines.append("")
        (out_dir / "assets.txt").write_text("\n".join(asset_lines), encoding="utf-8")
        css_dir = out_dir / "css"
        css_dir.mkdir(exist_ok=True)
        for css_url in assets.get("css", [])[:18]:
            full = urljoin(page.url, css_url)
            if not same_or_public(page.url, full):
                continue
            text = fetch_text(full)
            if text:
                (css_dir / f"{safe_name(urlparse(full).path.replace('/', '_'))}.css").write_text(text[:1_800_000], encoding="utf-8")
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(url, wait_until="domcontentloaded", timeout=55_000)
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        time.sleep(0.8)
        page.screenshot(path=str(out_dir / "mobile.png"), full_page=False)
        page.set_viewport_size({"width": 1440, "height": 900})
        info["ok"] = True
        info["extract"] = extract
    except Exception as exc:
        info["errors"].append(str(exc))
    return info


def write_summary(results: list[dict], out_root: Path) -> None:
    lines = ["# Design Reference Library", "", f"Generated refs: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for r in results:
        lines.append(f"## {r['name']}")
        lines.append(f"- URL: {r['url']}")
        lines.append(f"- OK: {r.get('ok')}")
        if r.get("title"):
            lines.append(f"- Title: {r['title']}")
        if r.get("errors"):
            lines.append(f"- Errors: {'; '.join(r['errors'])}")
        data = r.get("extract") or {}
        if data.get("headings"):
            lines.append("- Headings:")
            for h in data["headings"][:5]:
                text = h.get("text") or ""
                lines.append(f"  - {h.get('tag')} {h.get('size')} {h.get('weight')}: {text[:120]}")
        if data.get("colors"):
            lines.append("- Top colors: " + ", ".join(list(data["colors"].keys())[:8]))
        if data.get("fonts"):
            lines.append("- Top fonts: " + ", ".join(list(data["fonts"].keys())[:6]))
        if data.get("buttons"):
            lines.append("- Buttons/CTAs:")
            for b in data["buttons"][:5]:
                lines.append(f"  - {b.get('text')[:80]} | bg {b.get('bg')} | radius {b.get('radius')}")
        lines.append("")
    lines.extend([
        "## How to use",
        "- Use screenshots for visual direction and spacing.",
        "- Use extract.json for colors, fonts, headings, buttons, assets, and section structure.",
        "- Use downloaded CSS only as reference; rebuild original components in the target project.",
    ])
    (out_root / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="C:/projeto_ai/design-reference-library")
    parser.add_argument("--only", default="", help="Comma-separated site ids")
    args = parser.parse_args()
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    selected = SITES
    if args.only.strip():
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        selected = [s for s in SITES if s[0] in wanted]
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36",
        )
        page = context.new_page()
        for name, url in selected:
            print(f"Mining {name}: {url}", flush=True)
            result = scrape_site(page, name, url, out_root)
            print(f"  ok={result.get('ok')} title={result.get('title', '')[:80]}", flush=True)
            slim = dict(result)
            if "extract" in slim:
                slim["extract_path"] = f"{name}/extract.json"
                slim.pop("extract", None)
            results.append(result)
        browser.close()
    (out_root / "scraped.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(results, out_root)
    print(f"\nDone: {out_root}")
    print(f"Summary: {out_root / 'summary.md'}")


if __name__ == "__main__":
    main()
