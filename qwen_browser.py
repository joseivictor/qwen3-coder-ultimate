"""
Qwen Browser Automation — Playwright-powered browser control.
Supports open, click, type, screenshot, JS execution, scraping and more.
"""

import os, base64, time
from pathlib import Path
from typing import Optional

SCREENSHOT_DIR = Path("qwen_screenshots")


class BrowserAutomation:
    """Full browser control via Playwright sync API."""

    def __init__(self, headless: bool = False):
        self.headless  = headless
        self._pw       = None
        self._browser  = None
        self._context  = None
        self._page     = None
        SCREENSHOT_DIR.mkdir(exist_ok=True)

    def _ensure(self):
        if self._page and not self._page.is_closed():
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("Install playwright: pip install playwright && playwright install chromium")
        self._pw      = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self._page = self._context.new_page()

    # ── NAVIGATION ────────────────────────────────────────────────────────────
    def open(self, url: str, wait: str = "networkidle") -> str:
        self._ensure()
        try:
            self._page.goto(url, wait_until=wait, timeout=30000)
            return f"✅ Opened: {url}\nTitle: {self._page.title()}\nURL: {self._page.url}"
        except Exception as e:
            return f"Error opening {url}: {e}"

    def navigate_back(self) -> str:
        self._ensure()
        self._page.go_back()
        return f"Back → {self._page.url}"

    def reload(self) -> str:
        self._ensure()
        self._page.reload()
        return f"Reloaded: {self._page.url}"

    # ── INTERACTION ───────────────────────────────────────────────────────────
    def click(self, selector: str, timeout: int = 5000) -> str:
        self._ensure()
        try:
            self._page.click(selector, timeout=timeout)
            return f"✅ Clicked: {selector}"
        except Exception as e:
            return f"Click failed ({selector}): {e}"

    def type_text(self, selector: str, text: str, clear: bool = True) -> str:
        self._ensure()
        try:
            if clear:
                self._page.fill(selector, "")
            self._page.type(selector, text, delay=30)
            return f"✅ Typed in {selector}: {text[:50]}"
        except Exception as e:
            return f"Type failed ({selector}): {e}"

    def select_option(self, selector: str, value: str) -> str:
        self._ensure()
        try:
            self._page.select_option(selector, value)
            return f"✅ Selected '{value}' in {selector}"
        except Exception as e:
            return f"Select failed: {e}"

    def press_key(self, key: str) -> str:
        self._ensure()
        self._page.keyboard.press(key)
        return f"✅ Pressed: {key}"

    def hover(self, selector: str) -> str:
        self._ensure()
        try:
            self._page.hover(selector)
            return f"✅ Hovered: {selector}"
        except Exception as e:
            return f"Hover failed: {e}"

    def scroll(self, direction: str = "down", amount: int = 500) -> str:
        self._ensure()
        delta = amount if direction == "down" else -amount
        self._page.mouse.wheel(0, delta)
        return f"✅ Scrolled {direction} {amount}px"

    def wait_for(self, selector: str, timeout: int = 10000) -> str:
        self._ensure()
        try:
            self._page.wait_for_selector(selector, timeout=timeout)
            return f"✅ Element found: {selector}"
        except Exception as e:
            return f"Timeout waiting for {selector}: {e}"

    # ── EXTRACTION ────────────────────────────────────────────────────────────
    def get_text(self, selector: str = "body", limit: int = 5000) -> str:
        self._ensure()
        try:
            text = self._page.inner_text(selector)
            return text[:limit]
        except Exception as e:
            return f"Get text failed ({selector}): {e}"

    def get_html(self, selector: str = "body", limit: int = 8000) -> str:
        self._ensure()
        try:
            html = self._page.inner_html(selector)
            return html[:limit]
        except Exception as e:
            return f"Get HTML failed: {e}"

    def get_attribute(self, selector: str, attr: str) -> str:
        self._ensure()
        try:
            val = self._page.get_attribute(selector, attr)
            return str(val)
        except Exception as e:
            return f"Get attr failed: {e}"

    def get_links(self, filter_text: str = "") -> str:
        self._ensure()
        try:
            links = self._page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => ({text: e.innerText.trim(), href: e.href}))"
            )
            if filter_text:
                links = [l for l in links if filter_text.lower() in l["text"].lower()]
            return "\n".join(f"- {l['text'][:60]}: {l['href']}" for l in links[:30])
        except Exception as e:
            return f"Get links failed: {e}"

    def get_inputs(self) -> str:
        self._ensure()
        try:
            inputs = self._page.eval_on_selector_all(
                "input, textarea, select",
                "els => els.map(e => ({tag: e.tagName, type: e.type||'', name: e.name||'', id: e.id||'', placeholder: e.placeholder||''}))"
            )
            return "\n".join(
                f"- <{i['tag'].lower()} type={i['type']} name={i['name']} id={i['id']} placeholder={i['placeholder']}>"
                for i in inputs[:20]
            )
        except Exception as e:
            return f"Get inputs failed: {e}"

    # ── SCREENSHOT ────────────────────────────────────────────────────────────
    def screenshot(self, path: str = "", full_page: bool = False) -> str:
        self._ensure()
        if not path:
            path = str(SCREENSHOT_DIR / f"shot_{int(time.time())}.png")
        try:
            self._page.screenshot(path=path, full_page=full_page)
            size = os.path.getsize(path)
            return f"✅ Screenshot saved: {path} ({size:,} bytes)"
        except Exception as e:
            return f"Screenshot failed: {e}"

    def screenshot_element(self, selector: str, path: str = "") -> str:
        self._ensure()
        if not path:
            path = str(SCREENSHOT_DIR / f"element_{int(time.time())}.png")
        try:
            el = self._page.query_selector(selector)
            if el:
                el.screenshot(path=path)
                return f"✅ Element screenshot: {path}"
            return f"Element not found: {selector}"
        except Exception as e:
            return f"Element screenshot failed: {e}"

    # ── JAVASCRIPT ────────────────────────────────────────────────────────────
    def run_js(self, code: str) -> str:
        self._ensure()
        try:
            result = self._page.evaluate(code)
            return str(result)[:3000]
        except Exception as e:
            return f"JS error: {e}"

    def inject_css(self, css: str) -> str:
        self._ensure()
        self._page.add_style_tag(content=css)
        return "✅ CSS injected"

    # ── PAGE INFO ─────────────────────────────────────────────────────────────
    def page_info(self) -> str:
        self._ensure()
        return (f"URL: {self._page.url}\n"
                f"Title: {self._page.title()}\n"
                f"Viewport: {self._page.viewport_size()}")

    def get_console_logs(self) -> str:
        logs = []
        self._page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
        return "\n".join(logs[-20:]) if logs else "No console logs captured."

    # ── NETWORK ───────────────────────────────────────────────────────────────
    def intercept_requests(self, url_pattern: str = "*") -> str:
        """Log all network requests matching pattern."""
        captured = []
        def on_request(req):
            if url_pattern == "*" or url_pattern in req.url:
                captured.append(f"{req.method} {req.url}")
        self._page.on("request", on_request)
        return f"✅ Intercepting requests matching: {url_pattern}"

    # ── TABS ──────────────────────────────────────────────────────────────────
    def new_tab(self, url: str = "") -> str:
        self._ensure()
        self._page = self._context.new_page()
        if url:
            self._page.goto(url, wait_until="networkidle", timeout=30000)
        return f"✅ New tab opened. URL: {self._page.url}"

    # ── CLEANUP ───────────────────────────────────────────────────────────────
    def close(self) -> str:
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
            self._browser = self._page = self._context = self._pw = None
            return "✅ Browser closed."
        except Exception as e:
            return f"Close error: {e}"


# ── STANDALONE TEST ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    b = BrowserAutomation(headless=False)
    print(b.open("https://google.com"))
    print(b.screenshot())
    print(b.get_text("body", 500))
    b.close()
