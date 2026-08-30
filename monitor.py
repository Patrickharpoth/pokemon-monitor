from pathlib import Path
from dotenv import load_dotenv
import json
import os
import requests

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


def monitor_shop(shop_name, config):
    print(f"\n--- {shop_name} ---")
    current = config["scraper"]()
    snapshot_path = config["snapshot"]
    old = load_snapshot(snapshot_path)

    print(f"Produkter fundet: {len(current)}")

    # Safety: never overwrite a good snapshot if parsing fails.
    if not current:
        print("ADVARSEL: Ingen produkter fundet. Snapshot opdateres ikke.")
        return

    if old is None:
        save_snapshot(snapshot_path, current)
        print("Første kørsel - snapshot oprettet")
        return

    old_map = {product_key(p): p for p in old}
    current_map = {product_key(p): p for p in current}

    new_keys = set(current_map) - set(old_map)
    removed_keys = set(old_map) - set(current_map)
    changed = []

    for key in set(old_map) & set(current_map):
        before = old_map[key]
        now = current_map[key]
        if before.get("price") != now.get("price") or before.get("status") != now.get("status"):
            changed.append((before, now))

    if not (new_keys or removed_keys or changed):
        print("Ingen produktændringer")
        save_snapshot(snapshot_path, current)
        return

    lines = [
        f"🚨 {shop_name} Pokémon ændring fundet",
        f"Nye produkter: {len(new_keys)}",
        f"Fjernede produkter: {len(removed_keys)}",
        f"Pris/lager ændret: {len(changed)}",
        "",
    ]

    for key in sorted(new_keys):
        p = current_map[key]
        lines.append(f"🆕 {p['name']} | {p.get('price')} | {p.get('status')}\n{p.get('url', '')}")

    for key in sorted(removed_keys):
        p = old_map[key]
        lines.append(f"❌ {p['name']} | {p.get('price')} | {p.get('status')}")

    for before, now in changed:
        lines.append(
            f"🔄 {now['name']}\n"
            f"Før: {before.get('price')} | {before.get('status')}\n"
            f"Nu: {now.get('price')} | {now.get('status')}\n"
            f"{now.get('url', '')}"
        )

    message = "\n".join(lines)
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
