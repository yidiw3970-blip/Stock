"""Price-based factor calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_PRICE_COLUMNS = {"date", "ticker", "adj_close", "volume"}
OUTPUT_COLUMNS = [
    "date",
    "ticker",
    "momentum_20d",
    "momentum_60d",
    "momentum_120d",
    "momentum_252d",
    "volatility_60d",
    "max_drawdown_252d",
    "rolling_high_252d",
    "rolling_low_252d",
    "distance_to_52w_high",
    "distance_to_52w_low",
    "ma_50",
    "ma_200",
    "price_vs_ma_50",
    "price_vs_ma_200",
    "avg_dollar_volume_60d",
]


def compute_price_factors(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute price factors from normalized OHLCV data."""

    _require_columns(prices)
    df = prices.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df["adj_close"] = pd.to_numeric(df["adj_close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    frames = [
        _compute_single_ticker_factors(ticker_df)
        for _, ticker_df in df.groupby("ticker", sort=False)
    ]

    if not frames:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["date", "ticker"])
        .reset_index(drop=True)
    )


def _compute_single_ticker_factors(ticker_df: pd.DataFrame) -> pd.DataFrame:
    df = ticker_df.copy()
    price = df["adj_close"]
    volume = df["volume"]
    daily_return = price.pct_change()

    factors = pd.DataFrame(
        {
            "date": df["date"],
            "ticker": df["ticker"],
            "momentum_20d": price / price.shift(20) - 1,
            "momentum_60d": price / price.shift(60) - 1,
            "momentum_120d": price / price.shift(120) - 1,
            "momentum_252d": price / price.shift(252) - 1,
            "volatility_60d": daily_return.rolling(60, min_periods=60).std()
            * np.sqrt(252),
            "rolling_high_252d": price.rolling(252, min_periods=252).max(),
            "rolling_low_252d": price.rolling(252, min_periods=252).min(),
            "max_drawdown_252d": price.rolling(252, min_periods=252).apply(
                _max_drawdown,
                raw=True,
            ),
            "ma_50": price.rolling(50, min_periods=50).mean(),
            "ma_200": price.rolling(200, min_periods=200).mean(),
            "avg_dollar_volume_60d": (price * volume)
            .rolling(60, min_periods=60)
            .mean(),
        }
    )

    factors["distance_to_52w_high"] = price / factors["rolling_high_252d"] - 1
    factors["distance_to_52w_low"] = price / factors["rolling_low_252d"] - 1
    factors["price_vs_ma_50"] = price / factors["ma_50"] - 1
    factors["price_vs_ma_200"] = price / factors["ma_200"] - 1

    return factors.loc[:, OUTPUT_COLUMNS]


def _require_columns(prices: pd.DataFrame) -> None:
    missing_columns = REQUIRED_PRICE_COLUMNS.difference(prices.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"prices is missing required columns: {missing}")


def _max_drawdown(values: np.ndarray) -> float:
    running_high = np.maximum.accumulate(values)
    drawdowns = values / running_high - 1
    return float(np.nanmin(drawdowns))
