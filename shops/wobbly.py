import requests
from bs4 import BeautifulSoup
from .common import clean_space, extract_price, stock_from_danish, absolute

URLS = [
    "https://thewobblynerdles.dk/pokemon/",
    "https://thewobblynerdles.dk/pokemon-pre-orders/",
]
BASE = "https://thewobblynerdles.dk"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_products():
    products = {}
    session = requests.Session()
    session.headers.update(HEADERS)

    for url in URLS:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # WooCommerce cards.
        cards = soup.select("li.product, .product")
        for card in cards:
            link = card.select_one("a[href]")
            title = card.select_one(".woocommerce-loop-product__title, h2, h3")
            name = clean_space(title.get_text(" ", strip=True) if title else (link.get_text(" ", strip=True) if link else ""))
            if not link or not name:
                continue
            href = absolute(BASE, link.get("href"))
            card_text = clean_space(card.get_text(" ", strip=True))
            price = extract_price(card_text)
            status = stock_from_danish(card_text)
            if status is None:
                # WooCommerce product cards that have an add-to-cart button are buyable.
                if card.select_one(".add_to_cart_button, a.ajax_add_to_cart"):
                    status = "På lager"
                elif "udsOLGT".lower() in card_text.lower():
                    status = "Udsolgt"

            products[href] = {
                "name": name,
                "price": price,
                "status": status,
                "product_id": href,
                "url": href,
            }

    # Zero products can be legitimate only on preorder page, not both pages.
    if not products:
        raise RuntimeError("Wobbly blev hentet, men ingen Pokémon-produkter kunne udlæses")
    return list(products.values())
