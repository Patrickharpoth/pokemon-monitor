import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Intrafin URL configured to show the expanded Pokémon catalogue.
URL = "https://intrafin.eu/catalog/card-games/pokemon?q=H4sIAAAAAAAAA32QzwrCMAzG3yXnITg8yN7Ai3gfo8Q2jkjXjrYTZOzdzf7h3MFTyZcvX35pD9pijA4bggJuwZtOJ8hAe2c4sXcRih7aWT8sr9KYqPbhrdhAUfZgvUarHkxW6r%252FubPV2To%252FxYp%252B2NS0GjlN9uYryQtsJUZnn1VANGbRYS3nMIPqQNjsCWcJIysgOGTMcaM01FLVIT8%252FjEUIZqPGJVMK7pW%252BE2mPKzOLkzTU%252F8LtDp9b2x0qBFmYKauY%252Bn4YPwIXmE2kBAAA%253D"
BASE = "https://intrafin.eu"
TIMEOUT = 15

PRICE_RE = re.compile(r"(?:€|EUR)\s*[\d.,]+|[\d.,]+\s*(?:€|EUR)", re.I)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def normalize_status(text):
    value = (text or "").lower()
    if "out of stock" in value or "not in stock" in value or "sold out" in value:
        return "Udsolgt"
    if "backorder" in value or "back order" in value:
        return "Backorder"
    if "pre-order" in value or "preorder" in value:
        return "Pre-order"
    if "in stock" in value:
        return "På lager"
    return None

def get_products():
    session = requests.Session()
    session.headers.update(HEADERS)
    response = session.get(URL, timeout=TIMEOUT)
    response.raise_for_status()

    html = response.text
    lower = html.lower()
    if len(html) < 5000 or ("cloudflare" in lower and "challenge" in lower):
        raise RuntimeError("Intrafin returnerede ikke et normalt katalog")

    soup = BeautifulSoup(html, "html.parser")
    products = {}

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not href:
            continue
        full_url = urljoin(BASE, href)
        anchor_text = " ".join(a.stripped_strings).strip()

        # Keep the product name strictly to the anchor text. Parent/card text is
        # used only for stock and price so neighbouring accessory keywords cannot
        # accidentally make a sealed product ignored.
        if not anchor_text or len(anchor_text) < 4:
            continue

        card_text = anchor_text
        parent = a
        for _ in range(4):
            parent = getattr(parent, "parent", None)
            if parent is None:
                break
            candidate = " ".join(parent.stripped_strings).strip()
            if 10 <= len(candidate) <= 1500:
                card_text = candidate
            if PRICE_RE.search(candidate) and normalize_status(candidate):
                card_text = candidate
                break

        status = normalize_status(card_text)
        price_match = PRICE_RE.search(card_text)
        if not (price_match or status):
            continue

        lower_name = anchor_text.lower()
        if (
            lower_name in {
                "pokemon", "card games", "catalog", "catalogue",
                "next", "previous", "show more"
            }
            or lower_name.startswith("filter ")
            or full_url.lower().startswith("javascript:")
        ):
            continue

        products[full_url] = {
            "name": anchor_text,
            "price": price_match.group(0).strip() if price_match else None,
            "status": status,
            "product_id": full_url,
            "url": full_url,
        }

    if not products:
        raise RuntimeError("Intrafin-siden blev hentet, men ingen produkter kunne udlæses")

    return list(products.values())
