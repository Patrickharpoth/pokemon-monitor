import re
from playwright.sync_api import sync_playwright

URL = "https://www.proshop.dk/pokemon-kort?o=2052"

def normalize_status(text):
    if not text:
        return None
    checks = [
        ("Ikke på lager", "Ikke på lager"), ("Udsolgt", "Udsolgt"),
        ("Fjernlager", "Fjernlager"), ("Bestilt", "Bestilt"), ("På lager", "På lager"),
    ]
    for needle, normalized in checks:
        if needle.lower() in text.lower():
            return normalized
    return None

def is_price(text):
    return bool(re.match(r"^(?:\\d{1,3}(?:\\.\\d{3})*|\\d+),\\d{2}\\s*kr\\.$", text.strip()))

def is_product_id(text):
    return text.strip().isdigit() and len(text.strip()) >= 6

def is_valid_product_name(name):
    value = (name or "").strip()
    return value.lower() != "pokemon kort" and value.lower().startswith("pokemon") and len(value) > 7

def get_products():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)
        lines = [x.strip() for x in page.inner_text("body").splitlines() if x.strip()]
        browser.close()
    products, i = [], 0
    while i < len(lines):
        if not is_valid_product_name(lines[i]):
            i += 1; continue
        name, price, status, product_id, j = lines[i], None, None, None, i + 1
        while j < len(lines) and not lines[j].lower().startswith("pokemon"):
            cur = lines[j]
            if price is None and is_price(cur): price = cur
            normalized = normalize_status(cur)
            if normalized: status = normalized
            if is_product_id(cur): product_id = cur
            j += 1
        products.append({"name": name, "price": price, "status": status, "product_id": product_id, "url": URL})
        i = j
    unique = {}
    for p in products: unique[p.get("product_id") or p["name"]] = p
    return list(unique.values())
