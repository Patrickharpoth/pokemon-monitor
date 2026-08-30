# Pokemon Monitor V2.1

Multi-shop Pokémon product monitor.

## Alert logic
The monitor alerts only when:
1. A new relevant product appears.
2. An existing relevant product transitions to `På lager`.

Price changes, removals, and out-of-stock transitions do not trigger alerts.

## Ignore list
Edit `config.py` to add product-name keywords that should never trigger alerts.

Current ignore keywords:
- Zygarde
- Battle Deck
- Portfolio
- Championship Deck

## Structure
- `monitor.py` – shared monitoring, snapshots and Slack alerts
- `config.py` – ignore rules
- `shops/proshop.py` – Proshop scraper
- `shops/` – future shop scrapers
- `snapshots/` – runtime state, ignored by Git
