"""Loads run configuration: credentials from the environment and the shopping list from input.json."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://www.saucedemo.com"
DEFAULT_TIMEOUT_MS = 30_000


class ConfigError(Exception):
    """Raised when required configuration or input is missing or malformed."""


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


@dataclass(frozen=True)
class Customer:
    first_name: str
    last_name: str
    zip: str


@dataclass(frozen=True)
class OrderInput:
    items: list[str]
    customer: Customer


@dataclass(frozen=True)
class Settings:
    base_url: str
    credentials: Credentials
    headless: bool
    timeout_ms: int


def load_settings() -> Settings:
    load_dotenv()  # optional .env file; real environment variables take precedence

    username = os.getenv("SAUCE_USERNAME")
    password = os.getenv("SAUCE_PASSWORD")
    missing = [name for name, value in (("SAUCE_USERNAME", username), ("SAUCE_PASSWORD", password)) if not value]
    if missing:
        raise ConfigError(f"Missing required environment variable(s): {', '.join(missing)}")

    try:
        timeout_ms = int(os.getenv("SAUCE_TIMEOUT_MS", DEFAULT_TIMEOUT_MS))
    except ValueError as exc:
        raise ConfigError("SAUCE_TIMEOUT_MS must be an integer number of milliseconds") from exc

    return Settings(
        base_url=os.getenv("SAUCE_BASE_URL", DEFAULT_BASE_URL),
        credentials=Credentials(username=username, password=password),
        headless=os.getenv("HEADLESS", "true").strip().lower() not in ("0", "false", "no"),
        timeout_ms=timeout_ms,
    )


def load_order_input(path: Path) -> OrderInput:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Input file {path} is not valid JSON: {exc}") from exc

    items = data.get("items")
    if not isinstance(items, list) or not items or not all(isinstance(i, str) and i.strip() for i in items):
        raise ConfigError("'items' must be a non-empty list of product names")

    customer = data.get("customer") or {}
    fields = ("first_name", "last_name", "zip")
    missing = [f for f in fields if not str(customer.get(f, "")).strip()]
    if missing:
        raise ConfigError(f"'customer' is missing field(s): {', '.join(missing)}")

    return OrderInput(
        items=[i.strip() for i in items],
        customer=Customer(**{f: str(customer[f]).strip() for f in fields}),
    )
