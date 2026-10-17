"""Money parsing helpers. Decimal is used so that totals compare exactly (no float rounding)."""

import re
from decimal import Decimal

_AMOUNT = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")


def parse_money(text: str) -> Decimal:
    """Extract the dollar amount from strings like '$29.99' or 'Item total: $29.99'."""
    match = _AMOUNT.search(text)
    if not match:
        raise ValueError(f"Could not find a price in {text!r}")
    return Decimal(match.group(1))


def to_number(amount: Decimal) -> float:
    """Convert to a plain JSON number with two decimals."""
    return float(amount.quantize(Decimal("0.01")))
