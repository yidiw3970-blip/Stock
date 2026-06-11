"""Download research prototype price data with yfinance."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from stock_alpha_lab.data_sources.universe import load_supply_chain_map
from stock_alpha_lab.data_sources.yfinance_client import (
    download_price_history,
    save_prices_csv,
)

DEFAULT_SUPPLY_CHAIN_MAP = Path("data/watchlists/supply_chain_map.csv")
DEFAULT_OUTPUT_PATH = Path("data/raw/prices.csv")
DEFAULT_START_DATE = "2020-01-01"
DEFAULT_SLEEP_SECONDS = 2.0
DEFAULT_MAX_RETRIES = 2


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Download research prototype OHLCV data with yfinance."
    )
    parser.add_argument("--start", default=DEFAULT_START_DATE)
    parser.add_argument("--end", default=None)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument(
        "--tickers",
        default=None,
        help="Optional comma-separated tickers, for example: NVDA,MU",
    )
    parser.add_argument("--sleep-seconds", type=float, default=DEFAULT_SLEEP_SECONDS)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    return parser.parse_args(argv)


def main() -> int:
    """Run the yfinance price update workflow."""

    args = parse_args()
    tickers = parse_tickers(args.tickers)

    if not tickers:
        universe = load_supply_chain_map(DEFAULT_SUPPLY_CHAIN_MAP)
        tickers = universe["ticker"].tolist()

    prices = download_price_history(
        tickers=tickers,
        start=args.start,
        end=args.end,
        sleep_seconds=args.sleep_seconds,
        max_retries=args.max_retries,
    )
    save_prices_csv(prices, args.output)

    print(f"Saved {len(prices)} rows to {args.output}")
    print("Research only. Not financial advice. No auto-trading.")
    return 0


def parse_tickers(raw_tickers: str | None) -> list[str]:
    """Parse optional comma-separated tickers."""

    if not raw_tickers:
        return []

    return [
        ticker.strip().upper()
        for ticker in raw_tickers.split(",")
        if ticker.strip()
    ]


if __name__ == "__main__":
    raise SystemExit(main())
