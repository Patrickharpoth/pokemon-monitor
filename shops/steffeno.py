import time
import requests
from bs4 import BeautifulSoup
from .common import clean_space, extract_price, stock_from_danish, absolute

URL = "https://steffen-o.dk/shop/16-pokemon/"
BASE = "https://steffen-o.dk"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def _fetch():
    session = requests.Session()
    session.headers.update(HEADERS)
    last_error = None
    for attempt in range(2):
        try:
            response = session.get(URL, timeout=15)
            response.raise_for_status()
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(3)
    raise RuntimeError(f"Steffen O kunne ikke hentes efter 2 forsøg: {type(last_error).__name__}")

def get_products():
    response = _fetch()
    soup = BeautifulSoup(response.text, "html.parser")
    products = {}

    # Product links on the category page. Use surrounding container for stock/price.
    for a in soup.find_all("a", href=True):
        name = clean_space(a.get_text(" ", strip=True))
        href = absolute(BASE, a.get("href"))

        if not name or len(name) < 6:
            continue
        if name.lower() == "vis produkt":
            continue
        if "pokemon" not in name.lower() and "pokémon" not in name.lower():
            continue
        if href.rstrip("/") == URL.rstrip("/"):
            continue

        card = a
        card_text = name
        for _ in range(6):
            card = getattr(card, "parent", None)
            if card is None:
                break
            candidate = clean_space(card.get_text(" ", strip=True))
            if 10 < len(candidate) < 1800:
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
