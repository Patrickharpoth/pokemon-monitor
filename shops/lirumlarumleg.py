import requests

URL = "https://www.lirumlarumleg.dk/collections/pokemon"
JSON_URL = URL + "/products.json?limit=250"

def get_products():
    response = requests.get(JSON_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    data = response.json()
    products = []
    for p in data.get("products", []):
        variants = p.get("variants", [])
        available = any(v.get("available") for v in variants)
        prices = [v.get("price") for v in variants if v.get("price")]
        price = f"{prices[0]} kr." if prices else None
        handle = p.get("handle")
        products.append({
            "name": p.get("title") or "",
            "price": price,
            "status": "På lager" if available else "Udsolgt",
            "product_id": str(p.get("id")),
            "url": f"https://www.lirumlarumleg.dk/products/{handle}" if handle else URL,
        })
    return products
