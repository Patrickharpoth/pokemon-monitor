import re
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from .common import clean_space, extract_price, stock_from_danish, absolute

URL = "https://steffen-o.dk/shop/16-pokemon/"
BASE = "https://steffen-o.dk"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"}

def _is_product_name(line):
    value = clean_space(line)
    low = value.lower()
    return len(value) >= 8 and (low.startswith("pokemon ") or low.startswith("pokémon "))

def _parse_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Map visible product titles to their real product URLs.
    href_by_name = {}
    for a in soup.find_all("a", href=True):
        name = clean_space(a.get_text(" ", strip=True))
        if _is_product_name(name):
            href_by_name[name.casefold()] = absolute(BASE, a.get("href"))

    # This shop's category markup is unusual, but its visible text is stable:
    # product name -> "På lager"/"Udsolgt" -> price -> "Vis produkt".
    body = soup.body or soup
    lines = [clean_space(x) for x in body.get_text("\n", strip=True).splitlines() if clean_space(x)]

    products = {}
    for i, line in enumerate(lines):
        if not _is_product_name(line):
            continue

        status = None
        price = None
        for cur in lines[i + 1:i + 10]:
            if status is None:
                status = stock_from_danish(cur)
            if price is None:
                price = extract_price(cur)
            if cur.lower() == "vis produkt":
                break

        href = href_by_name.get(line.casefold(), URL)
        key = href if href != URL else line.casefold()
        products[key] = {
            "name": line,
            "price": price,
            "status": status,
            "product_id": href if href != URL else line,
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
            last_error = RuntimeError("ingen produkter i HTML")
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
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()
    return _parse_html(html)

def get_products():
    products = _requests_fetch()
    if not products:
        products = _browser_fetch()
    if not products:
        raise RuntimeError("Steffen O kunne ikke udlæses med hverken HTTP eller browser")
    return products
