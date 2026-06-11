"""Download research prototype price data with yfinance."""

from __future__ import annotations

import argparse
from pathlib import Path

from stock_alpha_lab.data_sources.universe import load_supply_chain_map
from stock_alpha_lab.data_sources.yfinance_client import (
    download_price_history,
    save_prices_csv,
)

DEFAULT_SUPPLY_CHAIN_MAP = Path("data/watchlists/supply_chain_map.csv")
DEFAULT_OUTPUT_PATH = Path("data/raw/prices.csv")
DEFAULT_START_DATE = "2020-01-01"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Download research prototype OHLCV data with yfinance."
    )
    parser.add_argument("--start", default=DEFAULT_START_DATE)
    parser.add_argument("--end", default=None)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    return parser.parse_args()


def main() -> int:
    """Run the yfinance price update workflow."""

    args = parse_args()
    universe = load_supply_chain_map(DEFAULT_SUPPLY_CHAIN_MAP)
    tickers = universe["ticker"].tolist()

    prices = download_price_history(tickers=tickers, start=args.start, end=args.end)
    save_prices_csv(prices, args.output)

    print(f"Saved {len(prices)} rows to {args.output}")
    print("Research only. Not financial advice. No auto-trading.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
