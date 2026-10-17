# SauceDemo Order Bot

A Python + Playwright bot that logs in to <https://www.saucedemo.com>, scrapes the product catalogue, orders the items in a shopping list, checks the totals and records the outcome.

## What it does

1. Logs in with credentials from environment variables.
2. Collects every product's name, description and price (as a number) into `output/products.json`.
3. Reads `input.json`, adds the listed items to the cart, and checks out with the customer details from the same file.
   Items that don't exist in the catalogue (exact name match, no guessing) are skipped and reported.
4. On the checkout overview page, reads item total, tax and total. The run **fails** if the item total doesn't equal the
   sum of the collected prices (it also checks `item total + tax == total`, and that the cart/overview contain exactly the expected items).
5. Finishes the order and saves `output/confirmation.png`.
6. Always writes `output/result.json`, whether the run passed or failed.

## Setup

Requires Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Running

Credentials are read from `SAUCE_USERNAME` and `SAUCE_PASSWORD` (the test logins are listed on the saucedemo homepage).
You can export them, or copy `.env.example` to `.env`.

```powershell
$env:SAUCE_USERNAME = "standard_user"      # bash: export SAUCE_USERNAME=standard_user
$env:SAUCE_PASSWORD = "secret_sauce"
python -m saucebot                          # uses ./input.json, writes to ./output/
```

Works unchanged for the slow login user: `$env:SAUCE_USERNAME = "performance_glitch_user"`.

Options:

| Setting | Default | Purpose |
|---|---|---|
| `--input PATH` | `input.json` | Shopping list and customer details |
| `--output-dir PATH` | `output` | Where results are written |
| `HEADLESS` env var | `true` | Set `false` to watch the browser |
| `SAUCE_TIMEOUT_MS` env var | `30000` | Max wait for any page state |

The exit code is `0` on success and `1` on failure, so it can be chained in a scheduler/CI.

Unit tests for the parsing and validation logic: `python -m pytest`.

## Output

| File | Contents |
|---|---|
| `products.json` | `[{"name", "description", "price"}]` for every product |
| `result.json` | `status` (`success`/`failed`), `totals`, `ordered_items`, `missing_items`, `error`, `failed_step`, screenshot names, timestamps |
| `confirmation.png` | Confirmation page after a successful order |
| `failure.png` | Page state at the moment of failure (only on failure) |

Example from the included run (`output/`): `Sauce Labs Water Bottle` doesn't exist, so it's listed in `missing_items`; the backpack and onesie are ordered
(item total `37.98`, tax `3.04`, total `41.02`) and status is `success`.

On failure, `result.json` says what went wrong and where, e.g.:

```json
{ "status": "failed", "failed_step": "login", "error": "Login failed: Epic sadface: Sorry, this user has been locked out." }
```

## Design notes

- **No fixed sleeps.** Every step waits for a concrete page state (e.g. the first product card being visible, or an
  "Add to cart" button flipping to "Remove"). Where an action can either succeed or show an error (login, checkout form), the bot waits for
  *whichever appears first* and reports the site's own error message. This is why `performance_glitch_user` needs no special handling.
- **Money as `Decimal`.** Prices are parsed to `Decimal` so the total comparison is exact; they're written to JSON as numbers.
- **Selectors** use the site's `data-test` attributes, which are more stable than CSS classes or text.
- **Failures are never hidden.** Config errors, site errors, timeouts and total mismatches all end up in `result.json` with the step they happened in,
  plus a failure screenshot, and a non-zero exit code. `products.json` is written as soon as it's collected, so it survives a later failure.

Layout:

```
saucebot/
  __main__.py   CLI entry point
  bot.py        run orchestration, checks, result.json
  pages.py      page objects (one class per saucedemo page)
  config.py     env vars + input.json loading/validation
  money.py      price parsing
tests/          unit tests for the pure logic
```

## Running against 40 different websites

I'd split the bot into a site-independent workflow (login → collect catalogue → add items → checkout → verify → record result) and per-site adapters
that implement the same small interface (`login`, `collect_products`, `add_to_cart`, `checkout`, `read_totals`, …). Simple sites could be driven by a
config file of selectors and URLs rather than code, with code adapters only for sites that need custom logic. Credentials would come from a secrets manager keyed by site,
and each site would run as an isolated job (in parallel, with retries for transient errors, per-site timeouts) writing the same `result.json` schema,
so one dashboard can show which sites failed and why. Finally, I'd add a scheduled smoke run per site to catch selector breakage early, since with 40 sites something will always be changing.
