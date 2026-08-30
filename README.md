# Pokemon Monitor V2.6

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

## V2.4
- Intrafin uses the user's expanded-catalogue URL so all displayed Pokémon products are monitored.
- Intrafin ignore matching is applied only to each product's own name.
- Price/stock context may come from the surrounding product card, but neighbouring text is never used as the product name.

## V2.4.1
- Intrafin additionally ignores `Deck Box`.
- Filters obvious UI entries such as `Filter 36 results` / `javascript:void(0)` so they cannot generate alerts.

## V2.5
- Supports `--shop` so different shops can run at different frequencies.
- Proshop, Infinity Prints TCG and Lirum Larum Leg: intended every minute.
- Intrafin: intended every 5 minutes with a 45-second HTTP timeout.
- A failed Intrafin request never overwrites its snapshot.
- `cron-v2.5.txt` contains the intended cron lines.

## V2.6
- Adds ToySpace Pokémon.
- Adds Steffen O Pokémon.
- Adds The Wobbly Nerdles from both normal Pokémon and Pokémon pre-order pages; duplicate product URLs are merged.
- Intrafin uses a 20-second timeout, waits 3 seconds, and retries once before giving up.
- Includes `cron-v2.6.txt` with all fast shops every minute and Intrafin every 5 minutes.
