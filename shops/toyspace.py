import json
import requests
from bs4 import BeautifulSoup
from .common import clean_space, extract_price, stock_from_danish, absolute

URL = "https://toyspace.dk/samlekort/maerke-pokemon"
FALLBACK_URL = "https://toyspace.dk/samlekort/pokemon-kort"
BASE = "https://toyspace.dk"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def _from_jsonld(soup):
    products = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            item_list = node.get("itemListElement", [])
            for entry in item_list if isinstance(item_list, list) else []:
                item = entry.get("item", entry) if isinstance(entry, dict) else {}
                if not isinstance(item, dict):
                    continue
                name = clean_space(item.get("name"))
                href = item.get("url")
                if not name or not href or "pokemon" not in name.lower():
                    continue
                offers = item.get("offers") if isinstance(item.get("offers"), dict) else {}
                availability = str(offers.get("availability", "")).lower()
                status = "På lager" if "instock" in availability else ("Udsolgt" if "outofstock" in availability else None)
                price = offers.get("price")
                products[href] = {
                    "name": name,
                    "price": f"{price} kr." if price else None,
                    "status": status,
                    "product_id": href,
                    "url": href,
                }
    return products

def get_products():
    session = requests.Session()
    session.headers.update(HEADERS)
    response = session.get(URL, timeout=20)
    if response.status_code >= 400:
        response = session.get(FALLBACK_URL, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    products = _from_jsonld(soup)

    # HTML fallback / enrichment.
    for a in soup.find_all("a", href=True):
        name = clean_space(a.get_text(" ", strip=True))
        if "pokemon" not in name.lower() or len(name) < 10:
            continue
        href = absolute(BASE, a["href"])
        if "/samlekort/" in href and href.rstrip("/") in {URL.rstrip("/"), FALLBACK_URL.rstrip("/")}:
            continue
        card = a
        card_text = name
        for _ in range(4):
            card = getattr(card, "parent", None)
            if card is None:
                break
            candidate = clean_space(card.get_text(" ", strip=True))
            if 10 < len(candidate) < 1200:
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
        raise RuntimeError("ToySpace blev hentet, men ingen Pokémon-produkter kunne udlæses")
    return list(products.values())
