import subprocess
import time
import requests
from bs4 import BeautifulSoup
from .common import clean_space, extract_price, stock_from_danish, absolute

URL = "https://toyspace.dk/samlekort/maerke-pokemon"
BASE = "https://toyspace.dk"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "da,en;q=0.8",
    "Connection": "close",
}

def _parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    products = {}

    for card in soup.select("li.product-item, .product-item-info"):
        link = card.select_one("a.product-item-link[href]") or card.select_one("a[href]")
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
    last_error = None
    for attempt in range(2):
        try:
            r = requests.get(URL, headers=HEADERS, timeout=(10, 20))
            r.raise_for_status()
            products = _parse_html(r.text)
            if products:
                return products
            last_error = RuntimeError("ingen produktkort i HTTP-svaret")
        except Exception as exc:
            last_error = exc
        if attempt == 0:
            time.sleep(3)
    return None

def _curl_fetch():
    cmd = [
        "curl", "-4", "-sS", "-L", "--compressed",
        "--connect-timeout", "10",
        "--max-time", "35",
        "--retry", "1",
        "--retry-delay", "3",
        "-A", HEADERS["User-Agent"],
        URL,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return None

    if result.returncode != 0 or not result.stdout:
        return None

    return _parse_html(result.stdout)

def get_products():
    products = _requests_fetch()
    if not products:
        products = _curl_fetch()

    if not products:
        raise RuntimeError("ToySpace kunne ikke hentes via hverken requests eller IPv4 curl")

    return products
