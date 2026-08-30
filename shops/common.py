import re
from urllib.parse import urljoin

PRICE_PATTERNS = [
    re.compile(r"(\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?)\s*(?:DKK|kr\.?|,-)", re.I),
    re.compile(r"(?:DKK|kr\.?)\s*(\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?)", re.I),
]

def clean_space(value):
    return " ".join((value or "").split())

def extract_price(text):
    text = clean_space(text)
    for pattern in PRICE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0).strip()
    return None

def stock_from_danish(text):
    value = clean_space(text).lower()
    # negative first
    if any(x in value for x in ("udsolgt", "ikke på lager", "ikke pÃ¥ lager")):
        return "Udsolgt"
    if any(x in value for x in ("køb nu", "put i kurven", "på lager", "pÃ¥ lager", "tilføj til kurv")):
        return "På lager"
    if "pre-order" in value or "preorder" in value or "forudbestil" in value:
        return "Pre-order"
    return None

def absolute(base, href):
    return urljoin(base, href or "")
