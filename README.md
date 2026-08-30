# Pokemon Monitor V2.3

Shops:
- Proshop
- Infinity Prints TCG
- Lirum Larum Leg
- Intrafin

## Alerts
Only:
- new relevant products
- existing relevant products changing to `På lager`

No alerts for price changes, removals, or products going out of stock.

## Ignore rules
Global: Zygarde, Battle Deck, Portfolio, Championship Deck.

Intrafin additionally: Sleeves, Album, Dispenser, Binder, Portfolio.

## V2.3 changes
- Lirum Larum Leg may legitimately return zero products; zero is saved as a valid baseline.
- Intrafin no longer launches a browser with a 60-second navigation timeout every minute.
- Product keys no longer fall back to a shared category URL.
- Includes a logrotate configuration for cron.log (5 MB, 3 compressed rotations).
- A shop failure does not overwrite its previous snapshot.
