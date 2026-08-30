GLOBAL_IGNORE_KEYWORDS = [
    "Zygarde",
    "Battle Deck",
    "Portfolio",
    "Championship Deck",
]

SHOP_IGNORE_KEYWORDS = {
    "Intrafin": [
        "Sleeves",
        "Album",
        "Dispenser",
        "Binder",
        "Portfolio",
    ],
}

# A zero-result scrape is normally treated as a failure.
# These shops are known to legitimately have zero matching products.
ALLOW_EMPTY_SHOPS = {
    "Lirum Larum Leg",
}


def is_ignored_product(name, shop_name=None):
    value = (name or "").lower()
    keywords = list(GLOBAL_IGNORE_KEYWORDS)
    if shop_name:
        keywords.extend(SHOP_IGNORE_KEYWORDS.get(shop_name, []))
    return any(keyword.lower() in value for keyword in keywords)
