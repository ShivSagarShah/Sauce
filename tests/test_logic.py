import json
from decimal import Decimal

import pytest

from saucebot.bot import split_found_and_missing, verify_totals
from saucebot.config import ConfigError, load_order_input
from saucebot.money import parse_money, to_number
from saucebot.pages import BotError, OrderTotals, Product


@pytest.mark.parametrize(
    "text, expected",
    [("$29.99", "29.99"), ("Item total: $37.98", "37.98"), ("Tax: $3.04", "3.04"), ("$ 7", "7")],
)
def test_parse_money(text, expected):
    assert parse_money(text) == Decimal(expected)


def test_parse_money_rejects_text_without_price():
    with pytest.raises(ValueError):
        parse_money("free")


def test_to_number_rounds_to_cents():
    assert to_number(Decimal("29.990")) == 29.99


def test_split_found_and_missing_is_exact_match():
    catalog = {"Sauce Labs Backpack": Product("Sauce Labs Backpack", "", Decimal("29.99"))}
    found, missing = split_found_and_missing(
        ["Sauce Labs Backpack", "sauce labs backpack", "Sauce Labs Water Bottle"], catalog
    )
    assert found == ["Sauce Labs Backpack"]
    assert missing == ["sauce labs backpack", "Sauce Labs Water Bottle"]


def test_verify_totals_passes_when_consistent():
    verify_totals(OrderTotals(Decimal("37.98"), Decimal("3.04"), Decimal("41.02")), Decimal("37.98"))


def test_verify_totals_fails_on_item_total_mismatch():
    with pytest.raises(BotError, match="Item total mismatch"):
        verify_totals(OrderTotals(Decimal("37.98"), Decimal("3.04"), Decimal("41.02")), Decimal("29.99"))


def test_verify_totals_fails_when_tax_does_not_add_up():
    with pytest.raises(BotError, match="Total mismatch"):
        verify_totals(OrderTotals(Decimal("37.98"), Decimal("3.04"), Decimal("50.00")), Decimal("37.98"))


def test_load_order_input(tmp_path):
    path = tmp_path / "input.json"
    path.write_text(
        json.dumps({"items": ["A"], "customer": {"first_name": "Ada", "last_name": "Lovelace", "zip": 94105}})
    )
    order = load_order_input(path)
    assert order.items == ["A"]
    assert order.customer.zip == "94105"


def test_load_order_input_reports_missing_customer_fields(tmp_path):
    path = tmp_path / "input.json"
    path.write_text(json.dumps({"items": ["A"], "customer": {"first_name": "Ada"}}))
    with pytest.raises(ConfigError, match="last_name, zip"):
        load_order_input(path)
