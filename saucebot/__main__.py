import argparse
import logging
import sys
from pathlib import Path

from .bot import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Log in to saucedemo.com, scrape products and place an order.")
    parser.add_argument("--input", type=Path, default=Path("input.json"), help="shopping list (default: input.json)")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="where to write results (default: output)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    result = run(args.input, args.output_dir)
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
