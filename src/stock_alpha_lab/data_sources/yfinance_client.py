"""yfinance price data helpers for research prototypes."""

from __future__ import annotations

import logging
import time
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
    tickers: list[str],
    start: str,
    end: str | None = None,
    sleep_seconds: float = 2.0,
    max_retries: int = 2,
) -> pd.DataFrame:
    """Download and normalize OHLCV price history for research use."""

    frames: list[pd.DataFrame] = []
    normalized_tickers = _normalize_tickers(tickers)

    for index, ticker in enumerate(normalized_tickers):
        downloaded = _download_single_ticker(
            ticker=ticker,
            start=start,
            end=end,
            sleep_seconds=sleep_seconds,
            max_retries=max_retries,
        )
        if downloaded is not None:
            frames.append(downloaded)

        if index < len(normalized_tickers) - 1:
            time.sleep(sleep_seconds)

    if not frames:
        raise RuntimeError(
            "Failed to download price history for all tickers. This may be a "
            "temporary yfinance/Yahoo rate limit. Try again later, reduce the "
            "number of tickers, increase sleep_seconds, or use a formal data "
            "source such as Polygon, Tiingo, or Alpha Vantage."
        )

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


def _download_single_ticker(
    ticker: str,
    start: str,
    end: str | None,
    sleep_seconds: float,
    max_retries: int,
) -> pd.DataFrame | None:
    attempts = max_retries + 1

    for attempt in range(1, attempts + 1):
        try:
            raw_df = yf.download(
                ticker,
                start=start,
                end=end,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            return normalize_yfinance_history(raw_df, ticker)
        except Exception as exc:  # noqa: BLE001
            if _is_rate_limit_error(exc):
                logger.warning(
                    "Rate limited while downloading %s on attempt %s/%s: %s",
                    ticker,
                    attempt,
                    attempts,
                    exc,
                )
                if attempt < attempts:
                    time.sleep(sleep_seconds)
                    continue
            else:
                logger.warning(
                    "Failed to download price history for %s on attempt %s/%s: %s",
                    ticker,
                    attempt,
                    attempts,
                    exc,
                )
            return None

    return None


def _is_rate_limit_error(exc: Exception) -> bool:
    message = f"{type(exc).__name__}: {exc}".lower()
    return any(
        marker in message
        for marker in ("rate limit", "ratelimit", "too many requests")
    )


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
