"""yfinance price data helpers for research prototypes."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import yfinance as yf

PRICE_COLUMNS = [
    "date",
    "ticker",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
]

CORE_PRICE_COLUMNS = {"open", "high", "low", "close", "volume"}

logger = logging.getLogger(__name__)


def normalize_yfinance_history(raw_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Normalize a single-ticker yfinance history DataFrame."""

    if raw_df.empty:
        raise ValueError(f"No price history returned for ticker '{ticker}'.")

    df = _flatten_columns(raw_df).copy()
    df = _move_index_to_date_column(df)
    df.columns = [_normalize_column_name(column) for column in df.columns]

    missing_columns = CORE_PRICE_COLUMNS.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Price history for ticker '{ticker}' is missing required columns: "
            f"{missing}"
        )

    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]

    df["date"] = _parse_datetimes_without_timezone(df["date"], ticker)
    df["ticker"] = ticker.strip().upper()

    normalized = df.loc[:, PRICE_COLUMNS].sort_values("date")
    return normalized.reset_index(drop=True)


def download_price_history(
    tickers: list[str], start: str, end: str | None = None
) -> pd.DataFrame:
    """Download and normalize OHLCV price history for research use."""

    frames: list[pd.DataFrame] = []

    for ticker in _normalize_tickers(tickers):
        try:
            raw_df = yf.download(
                ticker,
                start=start,
                end=end,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            frames.append(normalize_yfinance_history(raw_df, ticker))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to download price history for %s: %s", ticker, exc)

    if not frames:
        raise RuntimeError("Failed to download price history for all tickers.")

    return pd.concat(frames, ignore_index=True).sort_values(["ticker", "date"])


def save_prices_csv(df: pd.DataFrame, path: str | Path) -> None:
    """Save normalized prices to CSV."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.columns, pd.MultiIndex):
        return df

    flattened = df.copy()
    flattened.columns = [
        next((str(part) for part in column if str(part).strip()), "")
        for column in flattened.columns.to_flat_index()
    ]
    return flattened


def _move_index_to_date_column(df: pd.DataFrame) -> pd.DataFrame:
    if "Date" in df.columns or "date" in df.columns:
        return df

    index_name = df.index.name or "date"
    return df.reset_index(names=index_name)


def _normalize_column_name(column: object) -> str:
    return str(column).strip().lower().replace(" ", "_")


def _parse_datetimes_without_timezone(values: pd.Series, ticker: str) -> pd.Series:
    try:
        parsed = pd.to_datetime(values, errors="raise", utc=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Price history for ticker '{ticker}' contains invalid dates."
        ) from exc

    return parsed.dt.tz_localize(None)


def _normalize_tickers(tickers: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for ticker in tickers:
        symbol = ticker.strip().upper()
        if not symbol or symbol in seen:
            continue
        normalized.append(symbol)
        seen.add(symbol)

    return normalized
