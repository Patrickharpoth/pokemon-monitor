IGNORE_KEYWORDS = [
    "Zygarde",
    "Battle Deck",
    "Portfolio",
    "Championship Deck",
]


def is_ignored_product(name):
    name_lower = (name or "").lower()
    return any(keyword.lower() in name_lower for keyword in IGNORE_KEYWORDS)
