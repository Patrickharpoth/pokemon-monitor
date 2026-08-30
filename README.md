# Pokemon Monitor V2

Multi-shop Pokémon product monitor.

## Structure
- `monitor.py` – common monitoring, comparison and Slack alerts
- `shops/proshop.py` – Proshop scraper
- `shops/` – add future shops here
- `snapshots/` – runtime state; intentionally ignored by Git

The existing production scraper should remain active until V2 has been tested on the VPS.
