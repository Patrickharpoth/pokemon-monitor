import subprocess
import time
import requests
from bs4 import BeautifulSoup
from .common import clean_space, extract_price, stock_from_danish, absolute

URL = "https://steffen-o.dk/shop/16-pokemon/"
BASE = "https://steffen-o.dk"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "da,en;q=0.8",
    "Connection": "close",
}

def _is_product_name(text):
    value = clean_space(text)
    low = value.casefold()
    return len(value) >= 8 and (low.startswith("pokemon ") or low.startswith("pokémon "))

def _parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    products = {}

    # The category is server-rendered. Each product title is a link and
    # stock/price appear immediately after it in the visible category text.
    product_links = []
    for a in soup.find_all("a", href=True):
        name = clean_space(a.get_text(" ", strip=True))
        if _is_product_name(name):
            href = absolute(BASE, a.get("href"))
            # Same product can occur more than once in navigation/card markup.
            key = href if href and href != URL else name.casefold()
            product_links.append((key, name, href, a))

    for key, name, href, a in product_links:
        # Walk through nearby card/container text first.
        node = a
        context = ""
        for _ in range(7):
            node = getattr(node, "parent", None)
            if node is None:
                break
            candidate = clean_space(node.get_text(" ", strip=True))
            if 10 < len(candidate) < 1600:
                context = candidate
            if extract_price(candidate) and stock_from_danish(candidate):
                break

        price = extract_price(context)
        status = stock_from_danish(context)

        products[key] = {
            "name": name,
            "price": price,
            "status": status,
            "product_id": href if href and href != URL else name,
            "url": href or URL,
        }

    # If card ancestry is too broad/unusual, enrich from page text order.
    lines = [clean_space(x) for x in (soup.body or soup).get_text("\n", strip=True).splitlines() if clean_space(x)]
    by_name = {p["name"].casefold(): p for p in products.values()}
    for i, line in enumerate(lines):
        p = by_name.get(line.casefold())
        if not p:
            continue
        for cur in lines[i+1:i+9]:
            if p["status"] is None:
                p["status"] = stock_from_danish(cur)
            if p["price"] is None:
                p["price"] = extract_price(cur)
            if cur.casefold() == "vis produkt":
                break

    return list(products.values())

def _requests_fetch():
    last_error = None
    for attempt in range(2):
        try:
            r = requests.get(URL, headers=HEADERS, timeout=(10, 30))
            r.raise_for_status()
            products = _parse_html(r.text)
            if products:
                return products
            last_error = RuntimeError("ingen produkter i HTTP-svaret")
        except Exception as exc:
            last_error = exc
        if attempt == 0:
            time.sleep(3)
    return None

def _curl_fetch():
    # curl is used as a transport fallback because this shop's server
    # intermittently stalls connections from the VPS while still serving
    # normal server-rendered HTML to other clients.
    cmd = [
        "curl", "-sS", "-L", "--compressed",
        "--connect-timeout", "10",
        "--max-time", "45",
        "--retry", "1",
        "--retry-delay", "3",
        "-A", HEADERS["User-Agent"],
        URL,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=55)
    if result.returncode != 0:
        return None
    return _parse_html(result.stdout)

def get_products():
    products = _requests_fetch()
    if not products:
        products = _curl_fetch()
    if not products:
        raise RuntimeError("Steffen O kunne ikke hentes via hverken requests eller curl")
    return products
