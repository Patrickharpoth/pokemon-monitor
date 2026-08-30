from pathlib import Path
from dotenv import load_dotenv
import json
import os
import requests

from config import is_ignored_product
from shops.proshop import get_products as get_proshop_products

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SNAPSHOT_DIR = Path("snapshots")

SHOPS = {
    "Proshop": {
        "scraper": get_proshop_products,
        "snapshot": SNAPSHOT_DIR / "proshop.json",
    },
}


def send_slack_message(message):
    if not SLACK_WEBHOOK_URL:
        print("Slack webhook mangler i .env")
        return
    response = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=15)
    print("Slack status:", response.status_code, response.text)


def product_key(product):
    return product.get("product_id") or product.get("url") or product["name"]


def load_snapshot(path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_snapshot(path, products):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)


def is_in_stock(product):
    return product.get("status") == "På lager"


def monitor_shop(shop_name, config):
    print(f"\n--- {shop_name} ---")
    current = config["scraper"]()
    snapshot_path = config["snapshot"]
    old = load_snapshot(snapshot_path)

    print(f"Produkter fundet: {len(current)}")

    if not current:
        print("ADVARSEL: Ingen produkter fundet. Snapshot opdateres ikke.")
        return

    ignored_count = sum(is_ignored_product(p.get("name")) for p in current)
    print(f"Ignorerede produkter: {ignored_count}")

    if old is None:
        save_snapshot(snapshot_path, current)
        print("Første kørsel - snapshot oprettet")
        return

    old_map = {product_key(p): p for p in old}
    current_map = {product_key(p): p for p in current}

    new_products = []
    back_in_stock = []

    for key, product in current_map.items():
        if is_ignored_product(product.get("name")):
            continue

        if key not in old_map:
            new_products.append(product)
            continue

        before = old_map[key]

        # Only alert when a relevant product transitions from not-in-stock
        # (or unknown) to explicitly "På lager".
        if not is_in_stock(before) and is_in_stock(product):
            back_in_stock.append((before, product))

    if not new_products and not back_in_stock:
        print("Ingen relevante ændringer")
        save_snapshot(snapshot_path, current)
        return

    lines = [
        f"🚨 {shop_name} Pokémon alert",
        "",
    ]

    for p in new_products:
        lines.append(
            f"🆕 NYT PRODUKT\n"
            f"{p['name']}\n"
            f"Lager: {p.get('status') or 'Ukendt'}\n"
            f"Pris: {p.get('price') or 'Ikke fundet'}\n"
            f"{p.get('url', '')}"
        )

    for before, now in back_in_stock:
        lines.append(
            f"🟢 PÅ LAGER\n"
            f"{now['name']}\n"
            f"Før: {before.get('status') or 'Ukendt'}\n"
            f"Nu: På lager\n"
            f"Pris: {now.get('price') or 'Ikke fundet'}\n"
            f"{now.get('url', '')}"
        )

    message = "\n\n".join(lines)
    print(message)
    send_slack_message(message)
    save_snapshot(snapshot_path, current)


def main():
    for shop_name, config in SHOPS.items():
        try:
            monitor_shop(shop_name, config)
        except Exception as exc:
            print(f"FEJL i {shop_name}: {exc}")


if __name__ == "__main__":
    main()
