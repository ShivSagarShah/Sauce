"""Orchestrates one bot run and always produces result.json, whether the run succeeds or fails."""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from .config import ConfigError, OrderInput, Settings, load_order_input, load_settings
from .money import to_number
from .pages import (
    BotError,
    CartPage,
    CheckoutInfoPage,
    CheckoutOverviewPage,
    ConfirmationPage,
    InventoryPage,
    LoginPage,
    OrderTotals,
    Product,
)

log = logging.getLogger(__name__)


@dataclass
class RunResult:
    status: str = "failed"
    user: str | None = None
    requested_items: list[str] = field(default_factory=list)
    ordered_items: list[str] = field(default_factory=list)
    missing_items: list[str] = field(default_factory=list)
    totals: dict | None = None
    failed_step: str | None = None
    confirmation_message: str | None = None
    confirmation_screenshot: str | None = None
    failure_screenshot: str | None = None
    error: str | None = None
    current_step: str | None = field(default=None, repr=False)
    started_at: str = field(default_factory=lambda: _now())
    finished_at: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log.info("Wrote %s", path)


def _dedupe(items: list[str]) -> list[str]:
    unique = list(dict.fromkeys(items))
    if len(unique) != len(items):
        log.warning("Shopping list contains duplicates; each product can only be added once: %s", items)
    return unique


def split_found_and_missing(requested: list[str], catalog: dict[str, Product]) -> tuple[list[str], list[str]]:
    """Exact, case-sensitive name match. We never guess at a 'close enough' product."""
    found = [name for name in requested if name in catalog]
    missing = [name for name in requested if name not in catalog]
    return found, missing


def verify_totals(totals: OrderTotals, expected_item_total: Decimal) -> None:
    if totals.item_total != expected_item_total:
        raise BotError(
            f"Item total mismatch: checkout shows ${totals.item_total}, "
            f"but collected prices sum to ${expected_item_total}"
        )
    if totals.item_total + totals.tax != totals.total:
        raise BotError(
            f"Total mismatch: item total ${totals.item_total} + tax ${totals.tax} != total ${totals.total}"
        )


def _verify_same_items(where: str, actual: list[str], expected: list[str]) -> None:
    if sorted(actual) != sorted(expected):
        raise BotError(f"{where} contains {sorted(actual)}, expected {sorted(expected)}")


def _place_order(page: Page, settings: Settings, order: OrderInput, output_dir: Path, result: RunResult) -> None:
    result.current_step = "login"
    log.info("Logging in as %s", settings.credentials.username)
    LoginPage(page, settings.base_url).login(settings.credentials)

    result.current_step = "collect products"
    inventory = InventoryPage(page)
    products = inventory.collect_products()
    log.info("Collected %d products", len(products))
    _write_json(
        output_dir / "products.json",
        [{"name": p.name, "description": p.description, "price": to_number(p.price)} for p in products],
    )

    catalog = {p.name: p for p in products}
    found, missing = split_found_and_missing(result.requested_items, catalog)
    result.missing_items = missing
    for name in missing:
        log.warning("Item not found in catalog, skipping: %r", name)
    if not found:
        raise BotError("None of the requested items exist in the catalog; nothing to order")

    for name in found:
        result.current_step = f"add to cart: {name}"
        log.info("Adding to cart: %s", name)
        inventory.add_to_cart(name)
    result.ordered_items = found

    result.current_step = "cart"
    inventory.open_cart()
    cart = CartPage(page)
    _verify_same_items("Cart", cart.item_names(), found)
    cart.checkout()

    result.current_step = "checkout information"
    CheckoutInfoPage(page).submit(order.customer)

    result.current_step = "checkout overview"
    overview = CheckoutOverviewPage(page)
    _verify_same_items("Checkout overview", overview.item_names(), found)
    totals = overview.read_totals()
    expected_item_total = sum((catalog[name].price for name in found), Decimal("0"))
    result.totals = {
        "item_total": to_number(totals.item_total),
        "tax": to_number(totals.tax),
        "total": to_number(totals.total),
        "expected_item_total": to_number(expected_item_total),
    }
    log.info("Checkout totals: %s", result.totals)
    verify_totals(totals, expected_item_total)

    result.current_step = "finish order"
    overview.finish()
    result.confirmation_message = ConfirmationPage(page).wait_until_loaded()
    screenshot = output_dir / "confirmation.png"
    page.screenshot(path=str(screenshot), full_page=True)
    result.confirmation_screenshot = screenshot.name
    log.info("Order complete: %s", result.confirmation_message)


def _save_failure_screenshot(page: Page | None, output_dir: Path, result: RunResult) -> None:
    if page is None or page.is_closed():
        return
    path = output_dir / "failure.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        result.failure_screenshot = path.name
    except PlaywrightError as exc:
        log.warning("Could not capture failure screenshot: %s", exc)


def run(input_path: Path, output_dir: Path) -> RunResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in ("products.json", "result.json", "confirmation.png", "failure.png"):
        (output_dir / stale).unlink(missing_ok=True)

    result = RunResult()
    page: Page | None = None
    try:
        settings = load_settings()
        order = load_order_input(input_path)
        result.user = settings.credentials.username
        result.requested_items = _dedupe(order.items)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=settings.headless)
            try:
                context = browser.new_context()
                context.set_default_timeout(settings.timeout_ms)
                context.set_default_navigation_timeout(settings.timeout_ms)
                page = context.new_page()
                try:
                    _place_order(page, settings, order, output_dir, result)
                    result.status = "success"
                except Exception:
                    _save_failure_screenshot(page, output_dir, result)
                    raise
            finally:
                browser.close()
    except (ConfigError, BotError) as exc:
        result.error = str(exc)
    except PlaywrightError as exc:
        # Typically a timeout waiting for a page state; the first line is the useful part.
        result.error = f"Browser automation error: {str(exc).splitlines()[0]}"
    except Exception as exc:  # noqa: BLE001 - last resort so result.json is always written
        log.exception("Unexpected error")
        result.error = f"Unexpected error: {type(exc).__name__}: {exc}"
    finally:
        result.finished_at = _now()
        if result.error:
            result.failed_step = result.current_step or "setup"
            log.error("Run failed during %s: %s", result.failed_step, result.error)
        data = asdict(result)
        del data["current_step"]
        _write_json(output_dir / "result.json", data)

    return result
