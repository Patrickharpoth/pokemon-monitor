from playwright.sync_api import sync_playwright
import re

URLS = [
    "https://intrafin.eu/catalog/card-games/pokemon",
    "https://intrafin.eu/catalog/card-games/pokemon?page=2",
]

PRICE_RE = re.compile(r"€\\s*[\\d.,]+")

def get_products():
    products = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for url in URLS:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            # Intrafin exposes product links in the catalogue; capture link + nearby card text.
            links = page.locator('a[href*="/product/"], a[href*="/catalog/"]').all()
            for link in links:
                try:
                    text = (link.inner_text() or "").strip()
                    href = link.get_attribute("href")
                except Exception:
                    continue
                if not text or not href or "€" not in text:
                    continue
                if href.startswith("/"):
                    href = "https://intrafin.eu" + href
                match = PRICE_RE.search(text)
                price = match.group(0).strip() if match else None
                name = PRICE_RE.sub("", text).strip()
                if not name:
                    continue
                # Find stock state in the closest useful parent text.
                status = None
                try:
                    parent_text = link.locator("xpath=..").inner_text().lower()
                    if "in stock" in parent_text:
                        status = "På lager"
                    elif "backorder" in parent_text:
                        status = "Backorder"
                except Exception:
                    pass
                products[href] = {"name": name, "price": price, "status": status, "product_id": href, "url": href}
        browser.close()
    return list(products.values())
