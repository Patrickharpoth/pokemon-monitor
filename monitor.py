from pathlib import Path
import argparse
from dotenv import load_dotenv
import json
import os
import requests

from config import is_ignored_product, ALLOW_EMPTY_SHOPS
from shops.proshop import get_products as get_proshop_products
from shops.infinityprints import get_products as get_infinityprints_products
from shops.lirumlarumleg import get_products as get_lirumlarumleg_products
from shops.intrafin import get_products as get_intrafin_products

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SNAPSHOT_DIR = Path("snapshots")

SHOPS = {
    "Proshop": {"scraper": get_proshop_products, "snapshot": SNAPSHOT_DIR / "proshop.json"},
    "Infinity Prints TCG": {"scraper": get_infinityprints_products, "snapshot": SNAPSHOT_DIR / "infinityprints.json"},
    "Lirum Larum Leg": {"scraper": get_lirumlarumleg_products, "snapshot": SNAPSHOT_DIR / "lirumlarumleg.json"},
    "Intrafin": {"scraper": get_intrafin_products, "snapshot": SNAPSHOT_DIR / "intrafin.json"},
}


def send_slack_message(message):
    if not SLACK_WEBHOOK_URL:
        print("Slack webhook mangler i .env")
        return
    response = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=15)
    print("Slack status:", response.status_code, response.text)


def product_key(product):
    # Direct product URL is useful when available, but name is safer than
    # a shared category URL. Shop scrapers should provide a product_id where possible.
    return product.get("product_id") or product.get("name")


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

    if not current and shop_name not in ALLOW_EMPTY_SHOPS:
        print("ADVARSEL: Ingen produkter fundet. Snapshot opdateres ikke.")
        return

    ignored_count = sum(is_ignored_product(p.get("name"), shop_name) for p in current)
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
        if is_ignored_product(product.get("name"), shop_name):
            continue

        if key not in old_map:
            new_products.append(product)
            continue

        before = old_map[key]
        if not is_in_stock(before) and is_in_stock(product):
            back_in_stock.append((before, product))

    if not new_products and not back_in_stock:
        print("Ingen relevante ændringer")
        save_snapshot(snapshot_path, current)
        return

    lines = [f"🚨 {shop_name} Pokémon alert", ""]

    for p in new_products:
        lines.append(
            f"🆕 NYT PRODUKT\n{p['name']}\n"
            f"Lager: {p.get('status') or 'Ukendt'}\n"
            f"Pris: {p.get('price') or 'Ikke fundet'}\n"
            f"{p.get('url', '')}"
        )

    for before, now in back_in_stock:
        lines.append(
            f"🟢 PÅ LAGER\n{now['name']}\n"
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--shop",
        action="append",
        help="Kør kun en bestemt shop. Kan angives flere gange.",
    )
    args = parser.parse_args()

    selected = SHOPS
    if args.shop:
        requested = {name.lower() for name in args.shop}
        selected = {
            name: config
            for name, config in SHOPS.items()
            if name.lower() in requested
        }
        unknown = requested - {name.lower() for name in selected}
        if unknown:
            raise SystemExit("Ukendt shop: " + ", ".join(sorted(unknown)))

    for shop_name, config in selected.items():
        try:
            monitor_shop(shop_name, config)
        except Exception as exc:
            print(f"FEJL i {shop_name}: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
