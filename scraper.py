from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

import json
import os
import re
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


def normalize_status(status):
    if not status:
        return None

    if "På lager" in status:
        return "På lager"
    if "Fjernlager" in status:
        return "Fjernlager"
    if "Bestilt" in status:
        return "Bestilt"
    if "Udsolgt" in status:
        return "Udsolgt"
    if "Ikke på lager" in status:
        return "Ikke på lager"

    return status


def is_price(line):
    return bool(re.match(r"^\d{1,4},\d{2} kr\.$", line))


def is_product_id(line):
    return line.isdigit() and len(line) >= 6


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
        page.wait_for_timeout(10000)

        lines = [
            line.strip()
            for line in page.inner_text("body").splitlines()
            if line.strip()
        ]

        browser.close()

    products = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if not line.lower().startswith("pokemon"):
            i += 1
            continue

        name = line
        price = None
        status = None
        product_id = None

        j = i + 1

        while j < len(lines):
            current = lines[j]

            if current.lower().startswith("pokemon"):
                break

            if is_price(current) and price is None:
                price = current

            if (
                "På lager" in current
                or "Fjernlager" in current
                or "Bestilt" in current
                or "Udsolgt" in current
                or "Ikke på lager" in current
            ):
                status = normalize_status(current)

            if is_product_id(current):
                product_id = current

            j += 1

        products.append({
            "name": name,
            "price": price,
            "status": status,
            "product_id": product_id,
        })

        i = j

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
    return product.get("product_id") or product.get("name")


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
