from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

import json
import os
import requests

load_dotenv()

URL = "https://www.proshop.dk/pokemon-kort?o=2052"
SNAPSHOT_FILE = "snapshot.json"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_message(message):
    if not SLACK_WEBHOOK_URL:
        print("Slack webhook mangler i .env")
        return

    response = requests.post(
        SLACK_WEBHOOK_URL,
        json={"text": message},
        timeout=15
    )

    print("Slack status:", response.status_code, response.text)


def get_products():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)

        lines = [
            line.strip()
            for line in page.inner_text("body").splitlines()
            if line.strip()
        ]

        browser.close()

    products = []

    for i, line in enumerate(lines):
        if line.lower().startswith("pokemon"):
            price = None
            status = None
            product_id = None

            nearby_lines = lines[i:i + 35]

            for nearby in nearby_lines:
                if "kr." in nearby and price is None:
                    price = nearby

                if (
                    "På lager" in nearby
                    or "Fjernlager" in nearby
                    or "Bestilt" in nearby
                    or "Udsolgt" in nearby
                    or "Ikke på lager" in nearby
                ):
                    status = nearby

                if nearby.isdigit() and len(nearby) >= 6:
                    product_id = nearby

            products.append({
                "name": line,
                "price": price,
                "status": status,
                "product_id": product_id,
            })

    return products


def load_old_products():
    if not os.path.exists(SNAPSHOT_FILE):
        return None

    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_products(products):
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)


def product_key(product):
    if product.get("product_id"):
        return product["product_id"]

    return product["name"]


def main():
    current_products = get_products()
    old_products = load_old_products()

    print(f"Produkter fundet: {len(current_products)}")

    if not current_products:
        print("ADVARSEL: Ingen produkter fundet. Snapshot opdateres ikke.")
        return

    if old_products is None:
        save_products(current_products)
        print("Første kørsel - produkt snapshot oprettet")
        return

    old_map = {product_key(p): p for p in old_products}
    current_map = {product_key(p): p for p in current_products}

    old_keys = set(old_map.keys())
    current_keys = set(current_map.keys())

    new_keys = current_keys - old_keys
    removed_keys = old_keys - current_keys

    changed_products = []

    for key in old_keys & current_keys:
        old = old_map[key]
        current = current_map[key]

        if old.get("price") != current.get("price") or old.get("status") != current.get("status"):
            changed_products.append((old, current))

    if new_keys or removed_keys or changed_products:
        print("ÆNDRING FUNDET")

        message_lines = [
            "🚨 Proshop Pokémon ændring fundet",
            f"Nye produkter: {len(new_keys)}",
            f"Fjernede produkter: {len(removed_keys)}",
            f"Pris/lager ændret: {len(changed_products)}",
            "",
        ]

        for key in sorted(new_keys):
            product = current_map[key]
            line = f"🆕 {product['name']} | {product.get('price')} | {product.get('status')}"
            print(line)
            message_lines.append(line)

        for key in sorted(removed_keys):
            product = old_map[key]
            line = f"❌ {product['name']} | {product.get('price')} | {product.get('status')}"
            print(line)
            message_lines.append(line)

        for old, current in changed_products:
            line = (
                f"🔄 {current['name']}\n"
                f"Før: {old.get('price')} | {old.get('status')}\n"
                f"Nu: {current.get('price')} | {current.get('status')}"
            )
            print(line)
            message_lines.append(line)

        message_lines.append("")
        message_lines.append(URL)

        send_slack_message("\n".join(message_lines))
    else:
        print("Ingen produktændringer")

    save_products(current_products)

if __name__ == "__main__":
    main()