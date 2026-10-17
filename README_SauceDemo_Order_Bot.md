# SauceDemo Order Bot — Complete Project Guide

> A Python automation project that uses Playwright to log in to SauceDemo, read the product catalogue, add requested products to the cart, complete checkout, verify the order totals, and save a machine-readable result plus screenshots.

This guide explains the project from setup and first run through the implementation, every major feature, tests, output interpretation, troubleshooting, and safe ways to extend it.

---

## Contents

1. [Project at a glance](#project-at-a-glance)
2. [What the bot does](#what-the-bot-does)
3. [Technology and prerequisites](#technology-and-prerequisites)
4. [Project structure](#project-structure)
5. [Setup in IntelliJ IDEA](#setup-in-intellij-idea)
6. [Configure credentials and settings](#configure-credentials-and-settings)
7. [Configure the shopping order](#configure-the-shopping-order)
8. [Run the application](#run-the-application)
9. [End-to-end execution flow](#end-to-end-execution-flow)
10. [Feature-by-feature code walkthrough](#feature-by-feature-code-walkthrough)
11. [Output files and how to inspect them](#output-files-and-how-to-inspect-them)
12. [Run and understand the tests](#run-and-understand-the-tests)
13. [Errors and troubleshooting](#errors-and-troubleshooting)
14. [Configuration reference](#configuration-reference)
15. [Design decisions and reliability](#design-decisions-and-reliability)
16. [Limitations and extension ideas](#limitations-and-extension-ideas)
17. [Quick-start checklist](#quick-start-checklist)

---

## Project at a glance

| Item | Details |
|---|---|
| Project name | SauceDemo Order Bot (`saucebot`) |
| Language | Python |
| Browser automation | Playwright, synchronous Python API |
| Browser | Chromium |
| Target website | `https://www.saucedemo.com` by default |
| Input | `input.json` plus credentials from environment variables / `.env` |
| Main command | `python -m saucebot` |
| Main outputs | `output/products.json`, `output/result.json`, screenshots |
| Automated tests | `pytest` |

### Main purpose

The program automates a test shopping journey. It is not a general-purpose shopping bot and is currently written for SauceDemo's page structure and `data-test` selectors.

### High-level flow

```text
input.json + environment settings
              |
              v
     Validate configuration
              |
              v
     Launch Chromium / open site
              |
              v
       Log in to SauceDemo
              |
              v
   Read all products and prices
              |
              v
 Match requested names exactly
              |
              v
      Add found items to cart
              |
              v
 Verify cart -> enter customer data
              |
              v
 Read checkout totals and validate
              |
              v
       Finish the order
              |
              v
 Save confirmation screenshot + result.json
```

---

## What the bot does

1. Loads credentials and runtime settings.
2. Reads and validates the order in `input.json`.
3. Opens Chromium using Playwright and navigates to SauceDemo.
4. Signs in with the configured user.
5. Collects every product's name, description, and price from the inventory page and writes `output/products.json`.
6. Compares requested product names with the catalogue using an **exact, case-sensitive match**.
7. Logs missing items and skips them. Duplicate requested names are removed so the same product is not added twice.
8. Adds matching products to the cart.
9. Verifies that the cart contains exactly the products expected.
10. Enters first name, last name, and ZIP/postal code.
11. Verifies the checkout overview contains the expected products.
12. Reads item subtotal, tax, and total, then checks both:
    - Checkout item subtotal equals the sum of catalogue prices for the ordered products.
    - Item subtotal + tax equals the displayed total.
13. Finishes checkout, waits for the confirmation page, and saves `output/confirmation.png`.
14. Writes `output/result.json` for both successful and failed runs. If a browser-stage failure occurs, it also attempts to save `output/failure.png`.

**Important:** Missing items do not automatically fail the run if at least one requested item is found. If none of the requested items exist, the run fails without placing an order.

---

## Technology and prerequisites

- Python **3.10 or newer** is stated by the existing project documentation.
- IntelliJ IDEA or another Python-capable editor.
- Internet access to reach SauceDemo during a live run.
- The Python packages pinned in `requirements.txt`.
- Playwright's Chromium browser binary.

Dependencies:

| Package | Purpose |
|---|---|
| `playwright==1.63.0` | Controls Chromium and interacts with the website |
| `python-dotenv==1.2.4` | Loads optional settings from `.env` |
| `pytest==9.1.1` | Runs the automated unit tests |

Use a Python version compatible with the pinned package versions. If installation fails on a particular interpreter, select a supported Python release in IntelliJ and recreate the virtual environment.

---

## Project structure

The relevant project root is the `shiv/` directory inside the supplied archive.

```text
shiv/
├── .env.example          # Example environment configuration
├── input.json            # Requested products and customer checkout data
├── requirements.txt      # Pinned Python dependencies
├── pytest.ini             # Pytest discovery and import configuration
├── README.md               # Existing project notes
├── saucebot/
│   ├── __init__.py         # Package marker / short package description
│   ├── __main__.py         # CLI entry point: python -m saucebot
│   ├── bot.py              # Orchestration, matching, verification, results
│   ├── config.py           # Environment and input validation
│   ├── money.py            # Price parsing and JSON number conversion
│   └── pages.py            # Page objects and browser interactions
├── tests/
│   └── test_logic.py       # Unit tests for core logic
└── output/
    ├── products.json       # Catalogue captured by a previous run
    ├── result.json         # Result from a previous run
    └── confirmation.png    # Screenshot from a previous successful run
```

The archive may also contain `.venv/`, `.idea/`, and cached files. These are local environment/IDE artifacts, not application source code. A fresh setup should create its own virtual environment rather than relying on the one bundled in the archive.

### Which file should I read first?

- **To understand the whole run:** `saucebot/bot.py`
- **To understand browser actions and selectors:** `saucebot/pages.py`
- **To understand settings and input validation:** `saucebot/config.py`
- **To understand price handling:** `saucebot/money.py`
- **To understand how to launch it:** `saucebot/__main__.py`
- **To understand expected behaviour:** `tests/test_logic.py`

---

## Setup in IntelliJ IDEA

### 1. Open the correct folder

1. Extract `shivIntelliJ.zip`.
2. In IntelliJ IDEA, choose **Open** and select the `shiv/` folder (the folder containing `requirements.txt` and `saucebot/`).
3. Ensure IntelliJ recognises the folder as a Python project.
4. Configure a Python interpreter for the project.

Do not open only the `saucebot/` subfolder as the project root: the commands below assume the terminal's current directory is `shiv/`.

### 2. Create a virtual environment

Open IntelliJ's Terminal and run one of the following.

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If `py` is not available, try `python -m venv .venv`.

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Select this environment as the IntelliJ project interpreter if IntelliJ has not selected it automatically.

### 3. Install dependencies

Run from the `shiv/` project root:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

The last command downloads the Chromium binary Playwright needs. Installing the Python package alone does not necessarily install the browser binary.

### 4. Verify the setup

```bash
python --version
python -m pytest
```

The tests should run without opening a browser because they test parsing, validation, matching, and totals logic. A live application run is needed to test the website interactions themselves.

---

## Configure credentials and settings

The bot requires these environment variables:

- `SAUCE_USERNAME`
- `SAUCE_PASSWORD`

The simplest local option is to copy `.env.example` to `.env` in the project root and edit the values:

```dotenv
SAUCE_USERNAME=standard_user
SAUCE_PASSWORD=secret_sauce

# Optional settings:
# HEADLESS=false
# SAUCE_TIMEOUT_MS=30000
# SAUCE_BASE_URL=https://www.saucedemo.com
```

The example values are SauceDemo's commonly provided test credentials; confirm the current test credentials on the SauceDemo login page if they change.

### Windows PowerShell alternative

```powershell
$env:SAUCE_USERNAME = "standard_user"
$env:SAUCE_PASSWORD = "secret_sauce"
```

### macOS / Linux alternative

```bash
export SAUCE_USERNAME="standard_user"
export SAUCE_PASSWORD="secret_sauce"
```

Environment variables already present in the process take precedence over values loaded from `.env`. `config.py` calls `load_dotenv()` and then reads the environment.

**Credential hygiene:** Keep `.env` local, do not commit real credentials, and do not paste secrets into bug reports. The `.env.example` file is intended to contain placeholders or test-only values, not private credentials.

---

## Configure the shopping order

Edit `input.json` in the project root. The expected structure is:

```json
{
  "items": [
    "Sauce Labs Backpack",
    "Sauce Labs Onesie",
    "Sauce Labs Water Bottle"
  ],
  "customer": {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "zip": "94105"
  }
}
```

### `items`

- Must be a non-empty JSON array.
- Every entry must be a non-empty string.
- Product names must match the catalogue exactly, including case and spacing.
- Duplicate names are removed by the bot while preserving the first occurrence.
- Unknown names are skipped and listed in `missing_items`.
- If every requested item is missing, the run fails with a clear error.

The included example intentionally requests `Sauce Labs Water Bottle`; the existing example output indicates that this name was not found in the catalogue during that recorded run. Check the current catalogue before relying on that example.

### `customer`

All three values are required:

- `first_name`
- `last_name`
- `zip`

The loader converts these values to strings and trims surrounding whitespace. This means a numeric ZIP value is accepted and converted to text, but storing ZIP/postal codes as JSON strings is recommended to preserve leading zeros.

### Example: a smaller order

```json
{
  "items": ["Sauce Labs Backpack"],
  "customer": {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "zip": "094105"
  }
}
```

Use test data only. This project is intended for the SauceDemo test website.

---

## Run the application

Run all commands from the `shiv/` project root.

### Standard run

```bash
python -m saucebot
```

Defaults:
- Reads `input.json`.
- Writes generated files to `output/`.
- Runs Chromium headlessly because `HEADLESS` defaults to `true`.

### Watch the browser

Set `HEADLESS=false`.

**Windows PowerShell:**

```powershell
$env:HEADLESS = "false"
python -m saucebot
```

**macOS / Linux:**

```bash
HEADLESS=false python -m saucebot
```

A visible browser is useful when diagnosing selectors, navigation, or unexpected page content.

### Use another input file or output directory

```bash
python -m saucebot --input test-data/order.json --output-dir run-output
```

The input and output paths are interpreted relative to the current working directory unless absolute paths are provided.

### Check the exit code

- `0` means `result.status` is `success`.
- `1` means the run failed.

This is useful in scripts and CI pipelines. A run can still be considered successful when some requested items were missing, provided at least one valid item was ordered and the checkout completed with all validations passing.

---

## End-to-end execution flow

The CLI starts in `saucebot/__main__.py`:

1. `argparse` reads `--input` and `--output-dir`.
2. Logging is configured at `INFO`.
3. `run(input_path, output_dir)` is called from `saucebot.bot`.
4. The CLI returns exit code `0` or `1` based on the returned result status.

Inside `saucebot.bot.run()`:

1. Creates the output directory.
2. Deletes stale output files from the previous run (`products.json`, `result.json`, `confirmation.png`, `failure.png`) so they cannot be mistaken for current results.
3. Loads settings and validates `input.json`.
4. Removes duplicate requested product names.
5. Starts Playwright and launches Chromium in headless or visible mode.
6. Creates a browser context and page-level timeouts.
7. Calls `_place_order()` to perform the browser workflow.
8. Captures a failure screenshot if an exception occurs during the browser workflow.
9. Closes the browser in a `finally` block.
10. Converts expected configuration/business/browser errors into a readable `result.error`.
11. Writes `result.json` in the outer `finally` block regardless of success or failure.

The `current_step` field is used internally to track progress. Before writing JSON, it is removed from the serialized result; if a failure occurred, its value is copied to `failed_step`.

---

## Feature-by-feature code walkthrough

### 1. CLI entry point — `saucebot/__main__.py`

**Responsibility:** Provide the command-line interface.

Key behaviour:
- `--input`: path to the order JSON; defaults to `input.json`.
- `--output-dir`: path for output artifacts; defaults to `output`.
- Configures log lines with time and severity.
- Calls `run()`.
- Exits successfully only when the result status is `success`.

Use this file when adding new command-line options. Keep browser workflow logic in `bot.py`, rather than implementing it in the CLI.

### 2. Configuration and validation — `saucebot/config.py`

**Responsibility:** Read environment settings and validate the input order before browser work begins.

Important types:
- `Credentials`: username and password.
- `Customer`: first name, last name, ZIP/postal code.
- `OrderInput`: list of product names plus customer details.
- `Settings`: base URL, credentials, headless flag, timeout.
- `ConfigError`: raised for missing or malformed configuration.

`load_settings()`:
- Loads `.env` if available.
- Requires `SAUCE_USERNAME` and `SAUCE_PASSWORD`.
- Reads `SAUCE_BASE_URL`, defaulting to `https://www.saucedemo.com`.
- Reads `HEADLESS`; values `0`, `false`, and `no` (case-insensitive after trimming) disable headless mode. Other values enable it.
- Parses `SAUCE_TIMEOUT_MS` as an integer; invalid values raise `ConfigError`.

`load_order_input(path)`:
- Reads UTF-8 JSON.
- Gives a clear error for missing files or malformed JSON.
- Requires a non-empty list of non-empty strings in `items`.
- Requires all customer fields and trims their values.
- Returns typed `OrderInput` and `Customer` objects.

**Where to change things:** Add new input fields and their validation here, then update the relevant page object and tests.

### 3. Main workflow and orchestration — `saucebot/bot.py`

**Responsibility:** Coordinate the run and make sure results are reported.

`RunResult` is the result data model. It records:
- `status`
- `user`
- `requested_items`
- `ordered_items`
- `missing_items`
- `totals`
- `failed_step`
- `confirmation_message`
- `confirmation_screenshot`
- `failure_screenshot`
- `error`
- `started_at`
- `finished_at`

`split_found_and_missing(requested, catalog)`:
- Performs exact, case-sensitive name matching.
- Returns separate lists for found and missing names.
- Does not attempt fuzzy matching or guess a similar product.

`_dedupe(items)`:
- Removes duplicates while preserving order.
- Logs a warning if duplicates were present.

`_verify_same_items(where, actual, expected)`:
- Compares sorted lists, so order is not significant.
- Raises `BotError` if the cart or checkout overview has a different set of names. Duplicate occurrences would still cause a mismatch.

`verify_totals(totals, expected_item_total)`:
- Checks that the displayed item subtotal matches the sum of the selected catalogue prices.
- Checks that subtotal plus tax equals the displayed grand total.
- Raises `BotError` on either discrepancy.

`_place_order(...)` performs the steps in order:
1. Log in.
2. Collect the product catalogue and write `products.json`.
3. Match requested products and record missing names.
4. Fail if no requested products exist.
5. Add each found product to the cart.
6. Open the cart and verify its contents.
7. Start checkout and submit customer information.
8. Verify the checkout overview items.
9. Read and validate totals.
10. Finish the order, wait for the confirmation header, and save `confirmation.png`.

`run(...)` owns browser lifecycle and error handling. It catches:
- `ConfigError` and `BotError` as expected application failures.
- Playwright errors as browser automation errors.
- Other exceptions as unexpected errors, while logging the stack trace.

The result file is written from `finally`, which is a key reliability feature: failure details are retained even when the run does not complete.

### 4. Page objects and selectors — `saucebot/pages.py`

**Responsibility:** Encapsulate how the bot interacts with each website page. This is a Page Object Model (POM): workflow orchestration calls methods such as `login()` and `checkout()` without duplicating selectors everywhere.

Shared helpers:
- `by_test_id(scope, test_id)` creates a locator for `[data-test="..."]`.
- `wait_for_success_or_error(page, success, action)` waits for either the expected success element or the site's error banner. If the error banner is visible, it raises `BotError` with the website's message.

Page classes:

| Class | Role |
|---|---|
| `LoginPage` | Opens the base URL, fills credentials, clicks login, waits for inventory or an error |
| `InventoryPage` | Reads products, adds a named product, opens the cart |
| `CartPage` | Reads cart item names and proceeds to checkout |
| `CheckoutInfoPage` | Fills customer details and continues |
| `CheckoutOverviewPage` | Reads overview item names and totals, then finishes the order |
| `ConfirmationPage` | Waits for the completion header and returns its text |

Product and totals data models:
- `Product`: name, description, price (`Decimal`).
- `OrderTotals`: item subtotal, tax, and grand total (`Decimal`).

The locators use SauceDemo's `data-test` attributes, for example `username`, `password`, `login-button`, `inventory-item`, `checkout`, `firstName`, `subtotal-label`, and `complete-header`. These are preferred over fragile styling classes, but they are still tied to the target site's markup and can break if the site changes.

The code waits for visible elements or state changes instead of sleeping for a fixed duration. This makes it more resilient to variable load times.

### 5. Money helpers — `saucebot/money.py`

**Responsibility:** Parse displayed dollar values and convert `Decimal` values into JSON-compatible numbers.

`parse_money(text)`:
- Finds the first amount matching the project's dollar-price pattern, such as `$29.99`, `Item total: $29.99`, or `$ 7`.
- Returns a `Decimal`, not a binary floating-point value.
- Raises `ValueError` if no dollar amount is found.

`to_number(amount)`:
- Quantizes to two decimal places.
- Converts to a Python `float` for JSON output.

Why `Decimal` matters: currency calculations should not depend on binary floating-point rounding. The internal comparisons use exact decimal arithmetic; the JSON output is for convenient inspection and uses numeric values.

### 6. Automated tests — `tests/test_logic.py`

**Responsibility:** Check core business logic without launching a real browser.

The tests cover:
- Parsing prices in several text formats.
- Rejecting text that has no price.
- Converting a Decimal amount to two decimal places.
- Exact product-name matching and missing-product detection.
- Passing valid checkout totals.
- Rejecting mismatched item subtotals.
- Rejecting a grand total that does not equal subtotal plus tax.
- Loading a valid input order.
- Reporting missing customer fields.

`pytest.ini` sets `tests/` as the test directory and adds the project root to Python's import path.

These tests do **not** verify that SauceDemo is online, that selectors still match the live site, or that the entire checkout can complete. Those behaviours require a separate live browser run.

---

## Output files and how to inspect them

Every run cleans up stale output artifacts and then writes fresh output as execution progresses.

### `output/products.json`

Written immediately after the inventory catalogue has been collected. Each product contains:

```json
{
  "name": "Sauce Labs Backpack",
  "description": "A product description from the site",
  "price": 29.99
}
```

The file contains a JSON array of product objects. The exact product list and descriptions come from the live site at run time.

If this file exists after a failure later in checkout, the catalogue collection step probably completed.

### `output/result.json`

Written on both success and failure. Example success shape:

```json
{
  "status": "success",
  "user": "standard_user",
  "requested_items": ["Sauce Labs Backpack", "Sauce Labs Onesie"],
  "ordered_items": ["Sauce Labs Backpack", "Sauce Labs Onesie"],
  "missing_items": [],
  "totals": {
    "item_total": 37.98,
    "tax": 3.04,
    "total": 41.02,
    "expected_item_total": 37.98
  },
  "failed_step": null,
  "confirmation_message": "Thank you for your order!",
  "confirmation_screenshot": "confirmation.png",
  "failure_screenshot": null,
  "error": null,
  "started_at": "2026-01-01T10:00:00+00:00",
  "finished_at": "2026-01-01T10:00:10+00:00"
}
```

The values above illustrate the schema only; timestamps, message text, products, and totals depend on the actual run.

Fields to inspect first:
- `status`: `success` or `failed`.
- `failed_step`: step where failure was detected; normally `null` on success.
- `error`: human-readable failure reason; normally `null` on success.
- `requested_items`: de-duplicated requested names.
- `ordered_items`: requested names that were found and added.
- `missing_items`: requested names absent from the catalogue.
- `totals`: values read from checkout plus the calculated expected subtotal.
- `confirmation_screenshot` / `failure_screenshot`: screenshot filenames, if captured.
- `started_at` / `finished_at`: UTC timestamps.

### `output/confirmation.png`

Full-page screenshot captured after the confirmation header becomes visible. It is recorded only after the workflow reaches confirmation.

### `output/failure.png`

Best-effort full-page screenshot of the page state when a browser-stage exception occurs. Screenshot capture itself can fail if the page/browser has already closed; that is logged as a warning.

### Interpreting a failed run

1. Open `output/result.json`.
2. Read `failed_step`.
3. Read `error`.
4. If present, open `output/failure.png`.
5. Check the terminal log around the same step.
6. If `products.json` exists, inspect whether the inventory catalogue was captured correctly.

A failure before the browser workflow starts (for example, missing credentials or invalid input JSON) may not have a screenshot because no usable page exists yet.

---

## Run and understand the tests

From the project root:

```bash
python -m pytest
```

More detailed output:

```bash
python -m pytest -v
```

Run one test file:

```bash
python -m pytest tests/test_logic.py -v
```

Run a specific test by name:

```bash
python -m pytest -k verify_totals -v
```

A passing test suite confirms the tested logic behaves as expected. It does not guarantee the live website's selectors or end-to-end workflow are working.

### Suggested validation before changing code

1. Run the unit tests.
2. Make one focused code change.
3. Add or update a test for the changed behaviour.
4. Run the relevant test, then the full suite.
5. Run the bot against the SauceDemo test site with a small known-valid order.
6. Inspect `result.json` and the screenshot.

---

## Errors and troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `Missing required environment variable(s)` | Username/password not available to the process | Check `.env` location, spelling, and IntelliJ Run/Terminal environment |
| `Input file not found` | Incorrect working directory or `--input` path | Run from `shiv/` or pass the correct path |
| `is not valid JSON` | Syntax error in `input.json` | Check quotes, commas, braces, and brackets |
| `'items' must be a non-empty list...` | Wrong input shape or blank item | Ensure `items` is a JSON array of non-empty strings |
| `'customer' is missing field(s)` | Missing first name, last name, or ZIP | Supply all three fields |
| `SAUCE_TIMEOUT_MS must be an integer...` | Timeout setting is not numeric | Use a number such as `30000` |
| `Login failed: ...` | Invalid credentials, locked user, or site error | Read the site error in `result.json`; verify test credentials |
| `Item not found in catalog` | Product name differs from the live catalogue | Copy the exact name from `products.json` |
| `None of the requested items exist...` | Every requested product was missing | Correct `items` using exact catalogue names |
| `Cart contains ... expected ...` | Add-to-cart interaction or cart state differed | Inspect the screenshot and current site markup |
| `Item total mismatch` | Checkout subtotal differs from collected prices | Inspect `products.json`, checkout page, and selected products |
| `Total mismatch` | Displayed total is inconsistent with subtotal + tax | Inspect checkout values and currency parsing |
| Browser executable missing | Playwright Chromium has not been installed | Run `python -m playwright install chromium` |
| Timeout / browser automation error | Site is slow, unavailable, or a selector/state changed | Set `HEADLESS=false`, inspect screenshot, and consider a larger timeout |
| `ModuleNotFoundError: saucebot` | Wrong project root or interpreter | Run from `shiv/` with the project's virtual environment active |

### Useful debugging run

```powershell
$env:HEADLESS = "false"
$env:SAUCE_TIMEOUT_MS = "60000"
python -m saucebot
```

On macOS/Linux:

```bash
HEADLESS=false SAUCE_TIMEOUT_MS=60000 python -m saucebot
```

Increase timeouts only when the site genuinely needs more time. A longer timeout does not fix incorrect selectors or invalid input.

---

## Configuration reference

| Variable / argument | Required? | Default | Meaning |
|---|---:|---|---|
| `SAUCE_USERNAME` | Yes | None | SauceDemo login username |
| `SAUCE_PASSWORD` | Yes | None | SauceDemo login password |
| `SAUCE_BASE_URL` | No | `https://www.saucedemo.com` | Base URL to open |
| `HEADLESS` | No | `true` | `false`, `0`, or `no` shows the browser |
| `SAUCE_TIMEOUT_MS` | No | `30000` | Playwright default action/navigation timeout in milliseconds |
| `--input PATH` | No | `input.json` | Order input file |
| `--output-dir PATH` | No | `output` | Destination directory for generated artifacts |

`SAUCE_TIMEOUT_MS` is applied as both the page's default timeout and default navigation timeout. It is not a total-run time limit.

---

## Design decisions and reliability

### Exact matching rather than fuzzy matching

The bot will not silently substitute a similar product. This avoids ordering the wrong item. Missing products are explicitly reported.

### Decimal arithmetic for prices

Prices are parsed into `Decimal` and summed without binary floating-point rounding. The bot checks the displayed subtotal and the relationship between subtotal, tax, and total before finishing the order.

### Page Object Model

Browser selectors and interactions are concentrated in `pages.py`. The workflow in `bot.py` remains readable and easier to maintain. If SauceDemo changes a selector, the related page method is usually the first place to inspect.

### Explicit waits instead of fixed sleeps

The code waits for actual UI states: an inventory card becomes visible, an add button changes to Remove, a cart appears, or a confirmation header is visible. This is more reliable than sleeping for a guessed number of seconds.

### Always produce a result record

`result.json` is written in a `finally` block. This makes automated execution easier to monitor and gives a consistent place to look for status and errors.

### Browser cleanup

The browser is closed in a `finally` block, including when the workflow raises an exception.

### Stale output cleanup

Old output artifacts are removed at the start so an earlier successful screenshot cannot be mistaken for the result of a later failed run. Preserve or copy previous outputs elsewhere before rerunning if you need a historical record.

---

## Limitations and extension ideas

Current behaviour and scope:
- The selectors and page flow are tailored to SauceDemo.
- Product matching is exact and case-sensitive.
- Missing products are skipped if at least one product is found.
- The bot orders one instance of each unique requested product; quantities are not supported.
- There is no retry policy or persistent run history.
- The tests are unit tests, not browser end-to-end tests.
- Output timestamps are UTC.
- The money parser currently recognises dollar amounts only.
- The bot is designed for a test site and test data, not arbitrary production storefronts.

Possible improvements:
1. Add quantity support to the input schema and cart verification.
2. Add browser-level integration tests using a controlled test account.
3. Add structured log files and a run ID for easier CI troubleshooting.
4. Validate that `SAUCE_TIMEOUT_MS` is positive.
5. Add a configurable currency/parser if supporting another locale.
6. Add a summary report that highlights missing products and totals.
7. Separate website-specific page adapters from the general order workflow if expanding to multiple sites.
8. Add CI checks for unit tests and a controlled smoke test.
9. Keep credentials in a secrets manager for shared or CI environments.

When extending the project, preserve the principle that the bot should stop and report a discrepancy rather than silently proceeding with an unexpected cart or total.

---

## Quick-start checklist

- [ ] Open the extracted `shiv/` folder in IntelliJ.
- [ ] Select or create a compatible Python virtual environment.
- [ ] Install dependencies with `python -m pip install -r requirements.txt`.
- [ ] Install Chromium with `python -m playwright install chromium`.
- [ ] Create `.env` from `.env.example` or export credentials.
- [ ] Check product names and customer fields in `input.json`.
- [ ] Run `python -m pytest`.
- [ ] Run `python -m saucebot`.
- [ ] Inspect `output/result.json`.
- [ ] Open `output/confirmation.png` on success or `output/failure.png` when available.

**Most important debugging rule:** start with `output/result.json`, especially `failed_step` and `error`; then use the terminal logs, `products.json`, and screenshot to narrow down the issue.
