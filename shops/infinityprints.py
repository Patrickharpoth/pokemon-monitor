from playwright.sync_api import sync_playwright

URL = "https://www.infinityprints-tcg.com/category/sealed-products"

def get_products():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        # Wix product links on this category page.
        links = page.locator('a[href*="/product-page/"]')
        products = {}
        for i in range(links.count()):
            link = links.nth(i)
            name = (link.inner_text() or "").strip()
            href = link.get_attribute("href")
            if not name or not href:
                continue
            # Product title text may include "Price€..." on Wix.
            clean_name = name.split("Price€")[0].strip()
            if not clean_name:
                continue
            if href.startswith("/"):
                href = "https://www.infinityprints-tcg.com" + href
            products[href] = {"name": clean_name, "price": None, "status": None, "product_id": href, "url": href}

        # Enrich stock/price from the visible page text by matching product names.
        body = page.inner_text("body")
        lines = [x.strip() for x in body.splitlines() if x.strip()]
        for product in products.values():
            for idx, line in enumerate(lines):
                if product["name"] in line:
                    if "Price€" in line:
                        product["price"] = "€" + line.split("Price€", 1)[1].strip()
                    nearby = " ".join(lines[idx:idx+4]).lower()
                    if "out of stock" in nearby:
                        product["status"] = "Udsolgt"
                    elif "add to cart" in nearby:
                        product["status"] = "På lager"
                    break
        browser.close()
    return list(products.values())
