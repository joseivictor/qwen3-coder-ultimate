from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
URL = (ROOT / "index.html").as_uri()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(URL, wait_until="domcontentloaded")
    assert "Zion Lucas" in page.title()
    assert page.locator(".video-card").count() == 69
    assert page.locator(".video-card").evaluate_all(
        "cards => new Set(cards.map(card => card.dataset.video)).size"
    ) == 23
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    page.screenshot(path=str(ROOT / "screenshot-desktop.png"), full_page=False)
    page.locator(".video-card").nth(23).click()
    page.wait_for_timeout(500)
    assert not page.locator("#videoModal").evaluate("el => el.classList.contains('hidden')")
    page.screenshot(path=str(ROOT / "screenshot-modal.png"), full_page=False)
    page.locator("#modalClose").click()

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
    mobile.goto(URL, wait_until="domcontentloaded")
    assert mobile.locator(".video-card").count() == 69
    assert mobile.locator(".video-card").evaluate_all(
        "cards => new Set(cards.map(card => card.dataset.video)).size"
    ) == 23
    assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    mobile.screenshot(path=str(ROOT / "screenshot-mobile.png"), full_page=False)

    browser.close()
    if errors:
        raise SystemExit("\n".join(errors))

print("OK")
