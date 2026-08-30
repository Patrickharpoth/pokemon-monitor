import requests
from bs4 import BeautifulSoup
from .common import clean_space, extract_price, stock_from_danish, absolute

URL = "https://toyspace.dk/samlekort/maerke-pokemon"
BASE = "https://toyspace.dk"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_products():
    response = requests.get(URL, timeout=20, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    products = {}

    # Magento-style product cards.
    cards = soup.select(".product-item, li.product-item, .product-item-info")
    for card in cards:
        link = card.select_one("a.product-item-link[href], a[href]")
        if not link:
            continue

        name = clean_space(link.get_text(" ", strip=True))
        href = absolute(BASE, link.get("href"))
        if not name or not href or href.rstrip("/") == URL.rstrip("/"):
            continue

        card_text = clean_space(card.get_text(" ", strip=True))
        price = extract_price(card_text)
        status = stock_from_danish(card_text)

        # ToySpace shows "Køb nu" for buyable products and "Udsolgt" otherwise.
        if status is None:
            if "køb nu" in card_text.lower():
                status = "På lager"
            elif "udsolgt" in card_text.lower():
                status = "Udsolgt"

        products[href] = {
            "name": name,
            "price": price,
            "status": status,
            "product_id": href,
            "url": href,
        }

    if not products:
        raise RuntimeError("ToySpace blev hentet, men ingen produkter kunne udlæses")
    return list(products.values())
