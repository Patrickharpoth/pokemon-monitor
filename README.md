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

## V2.6.1
- ToySpace parser fixed to read every product card in the filtered Pokémon category instead of requiring the word Pokémon in every title.
- Steffen O now retries once after 3 seconds with a 15-second timeout.
- Recommended cron moves Steffen O to the 5-minute group because its server can be slow.

## V2.6.2
- ToySpace: HTTP with retry, then Playwright fallback; parses Magento product cards.
- Steffen O: parses the shop's stable visible-text structure instead of relying on generic product-card HTML.
- Steffen O also has HTTP retry and Playwright fallback.
- ToySpace's existing v2.6 snapshot should be deleted once before testing because v2.6 only captured 3 of 13 products.

## V2.6.3
- Steffen O no longer uses Playwright. The page is server-rendered, so the scraper now uses requests first and curl as a transport fallback.
- Product extraction is based on the shop's Pokemon title links and nearby stock/price text.
- ToySpace moved to the 5-minute group because its HTTP server can time out and trigger a browser fallback.
- Fast group remains Proshop, Infinity Prints TCG, Lirum Larum Leg, and The Wobbly Nerdles.

## V2.6.4 final
- The Wobbly Nerdles is enabled in the every-minute group.
- ToySpace is enabled in the every-5-minute group because its server can occasionally be slow.
- Steffen O remains in the codebase for future work but is not scheduled in cron.
