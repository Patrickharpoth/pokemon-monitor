import requests
from bs4 import BeautifulSoup
from .common import clean_space, extract_price, stock_from_danish, absolute

URL = "https://steffen-o.dk/shop/16-pokemon/"
BASE = "https://steffen-o.dk"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_products():
    response = requests.get(URL, timeout=20, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    products = {}

    # Find product-ish links, then use the surrounding card for stock/price.
    for a in soup.find_all("a", href=True):
        name = clean_space(a.get_text(" ", strip=True))
        href = absolute(BASE, a["href"])
        if not name or len(name) < 8:
            continue
        if "pokemon" not in name.lower() and "pokémon" not in name.lower():
            continue
        if href.rstrip("/") == URL.rstrip("/"):
            continue

        card = a
        card_text = name
        for _ in range(5):
            card = getattr(card, "parent", None)
            if card is None:
                break
            candidate = clean_space(card.get_text(" ", strip=True))
            if 10 < len(candidate) < 1500:
                card_text = candidate
            if extract_price(candidate) and stock_from_danish(candidate):
                break

        price = extract_price(card_text)
        status = stock_from_danish(card_text)
        if not (price or status):
            continue

        products[href] = {
            "name": name,
            "price": price,
            "status": status,
            "product_id": href,
            "url": href,
        }

    if not products:
        raise RuntimeError("Steffen O blev hentet, men ingen Pokémon-produkter kunne udlæses")
    return list(products.values())
