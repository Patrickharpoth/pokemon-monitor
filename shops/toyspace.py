import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from .common import clean_space, extract_price, stock_from_danish, absolute

URL = "https://toyspace.dk/samlekort/maerke-pokemon"
BASE = "https://toyspace.dk"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"}

def _parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    products = {}

    # ToySpace/Magento product cards.
    for card in soup.select("li.product-item, .product-item-info"):
        link = card.select_one("a.product-item-link[href]")
        if not link:
            # image links often wrap the same product; use only if no title link exists
            link = card.select_one("a[href]")
        if not link:
            continue

        name = clean_space(link.get_text(" ", strip=True))
        if not name:
            title = card.select_one(".product-item-name, .product.name")
            name = clean_space(title.get_text(" ", strip=True) if title else "")
        href = absolute(BASE, link.get("href"))

        if not name or not href or href.rstrip("/") == URL.rstrip("/"):
            continue

        card_text = clean_space(card.get_text(" ", strip=True))
        price = extract_price(card_text)
        status = stock_from_danish(card_text)
        if status is None:
            low = card_text.lower()
            if "køb nu" in low:
                status = "På lager"
            elif "udsolgt" in low or "giv mig besked" in low:
                status = "Udsolgt"

        products[href] = {
            "name": name,
            "price": price,
            "status": status,
            "product_id": href,
            "url": href,
        }

    return list(products.values())

def _requests_fetch():
    session = requests.Session()
    session.headers.update(HEADERS)
    last_error = None
    for attempt in range(2):
        try:
            response = session.get(URL, timeout=15)
            response.raise_for_status()
            products = _parse_html(response.text)
            if products:
                return products
            last_error = RuntimeError("ingen produktkort i HTML")
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as exc:
            last_error = exc
        if attempt == 0:
            time.sleep(3)
    return None

def _browser_fetch():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=HEADERS["User-Agent"])
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        html = page.content()
        browser.close()
    return _parse_html(html)

def get_products():
    products = _requests_fetch()
    if not products:
        products = _browser_fetch()
    if not products:
        raise RuntimeError("ToySpace kunne ikke udlæses med hverken HTTP eller browser")
    return products
