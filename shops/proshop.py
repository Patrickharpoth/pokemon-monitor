import re
from playwright.sync_api import sync_playwright

URL = "https://www.proshop.dk/pokemon-kort?o=2052"


def normalize_status(text):
    if not text:
        return None

    # Specific states first.
    checks = [
        ("Ikke på lager", "Ikke på lager"),
        ("Udsolgt", "Udsolgt"),
        ("Fjernlager", "Fjernlager"),
        ("Bestilt", "Bestilt"),
        ("På lager", "På lager"),
    ]
    for needle, normalized in checks:
        if needle.lower() in text.lower():
            return normalized
    return None


def is_price(text):
    return bool(re.match(r"^\d{1,3}(?:\.\d{3})*,\d{2}\s*kr\.$|^\d+,\d{2}\s*kr\.$", text.strip()))


def is_product_id(text):
    return text.strip().isdigit() and len(text.strip()) >= 6


def get_products():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)

        lines = [line.strip() for line in page.inner_text("body").splitlines() if line.strip()]
        browser.close()

    products = []
    i = 0

    # Segment text at the next Pokémon product instead of looking a fixed
    # number of lines ahead. This prevents data leaking from neighbouring cards.
    while i < len(lines):
        line = lines[i]
        if not line.lower().startswith("pokemon"):
            i += 1
            continue

        name = line
        price = None
        status = None
        product_id = None
        j = i + 1

        while j < len(lines):
            current = lines[j]
            if current.lower().startswith("pokemon"):
                break

            if price is None and is_price(current):
                price = current

            normalized = normalize_status(current)
            if normalized:
                status = normalized

            if is_product_id(current):
                product_id = current

            j += 1

        products.append({
            "name": name,
            "price": price,
            "status": status,
            "product_id": product_id,
            "url": URL,
        })
        i = j

    # Avoid duplicate identities corrupting comparisons.
    unique = {}
    for product in products:
        key = product.get("product_id") or product["name"]
        unique[key] = product

    return list(unique.values())
