"""Page objects for saucedemo.com.

Every wait here is on a concrete page state (an element becoming visible), never a fixed sleep.
Selectors use the site's data-test attributes, which are more stable than CSS classes.
"""

from dataclasses import dataclass
from decimal import Decimal

from playwright.sync_api import Locator, Page

from .config import Credentials, Customer
from .money import parse_money


class BotError(Exception):
    """A business-level failure that should be reported in result.json."""


@dataclass(frozen=True)
class Product:
    name: str
    description: str
    price: Decimal


@dataclass(frozen=True)
class OrderTotals:
    item_total: Decimal
    tax: Decimal
    total: Decimal


def by_test_id(scope: Page | Locator, test_id: str) -> Locator:
    return scope.locator(f'[data-test="{test_id}"]')


def wait_for_success_or_error(page: Page, success: Locator, action: str) -> None:
    """Wait until either the expected next state or the site's error banner appears."""
    error = by_test_id(page, "error")
    success.or_(error).first.wait_for(state="visible")
    if error.is_visible():
        raise BotError(f"{action} failed: {error.inner_text().strip()}")


class LoginPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def login(self, credentials: Credentials) -> None:
        self.page.goto(self.base_url)
        by_test_id(self.page, "username").fill(credentials.username)
        by_test_id(self.page, "password").fill(credentials.password)
        by_test_id(self.page, "login-button").click()
        # performance_glitch_user is slow here; we simply wait (up to the timeout) for the result.
        wait_for_success_or_error(self.page, by_test_id(self.page, "inventory-list"), "Login")


class InventoryPage:
    def __init__(self, page: Page):
        self.page = page
        self.items = by_test_id(page, "inventory-item")

    def collect_products(self) -> list[Product]:
        # The list container can appear before its cards render, so wait for an actual card.
        self.items.first.wait_for(state="visible")

        products = [
            Product(
                name=by_test_id(item, "inventory-item-name").inner_text().strip(),
                description=by_test_id(item, "inventory-item-desc").inner_text().strip(),
                price=parse_money(by_test_id(item, "inventory-item-price").inner_text()),
            )
            for item in self.items.all()
        ]
        if not products:
            raise BotError("No products found on the inventory page")
        return products

    def add_to_cart(self, product_name: str) -> None:
        names = [n.strip() for n in by_test_id(self.page, "inventory-item-name").all_inner_texts()]
        matches = [i for i, name in enumerate(names) if name == product_name]
        if len(matches) != 1:
            raise BotError(f"Expected exactly one product named {product_name!r}, found {len(matches)}")

        card = self.items.nth(matches[0])
        card.get_by_role("button", name="Add to cart").click()
        # Confirm the click registered: the card's button flips to "Remove".
        card.get_by_role("button", name="Remove").wait_for(state="visible")

    def open_cart(self) -> None:
        by_test_id(self.page, "shopping-cart-link").click()
        by_test_id(self.page, "cart-list").wait_for(state="visible")


def _item_names(page: Page) -> list[str]:
    return [n.strip() for n in by_test_id(page, "inventory-item-name").all_inner_texts()]


class CartPage:
    def __init__(self, page: Page):
        self.page = page

    def item_names(self) -> list[str]:
        return _item_names(self.page)

    def checkout(self) -> None:
        by_test_id(self.page, "checkout").click()
        by_test_id(self.page, "firstName").wait_for(state="visible")


class CheckoutInfoPage:
    def __init__(self, page: Page):
        self.page = page

    def submit(self, customer: Customer) -> None:
        by_test_id(self.page, "firstName").fill(customer.first_name)
        by_test_id(self.page, "lastName").fill(customer.last_name)
        by_test_id(self.page, "postalCode").fill(customer.zip)
        by_test_id(self.page, "continue").click()
        wait_for_success_or_error(self.page, by_test_id(self.page, "total-label"), "Checkout information")


class CheckoutOverviewPage:
    def __init__(self, page: Page):
        self.page = page

    def item_names(self) -> list[str]:
        return _item_names(self.page)

    def read_totals(self) -> OrderTotals:
        return OrderTotals(
            item_total=parse_money(by_test_id(self.page, "subtotal-label").inner_text()),
            tax=parse_money(by_test_id(self.page, "tax-label").inner_text()),
            total=parse_money(by_test_id(self.page, "total-label").inner_text()),
        )

    def finish(self) -> None:
        by_test_id(self.page, "finish").click()


class ConfirmationPage:
    def __init__(self, page: Page):
        self.page = page

    def wait_until_loaded(self) -> str:
        header = by_test_id(self.page, "complete-header")
        header.wait_for(state="visible")
        return header.inner_text().strip()
