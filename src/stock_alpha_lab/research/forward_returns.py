"""Forward return labels for factor validation research."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_PRICE_COLUMNS = {"date", "ticker", "adj_close"}
DEFAULT_HORIZONS = [20, 60, 120]
DEFAULT_BENCHMARK_TICKERS = ["SPY", "QQQ", "SMH"]

FORWARD_RETURN_COLUMNS = ["date", "ticker", "horizon", "forward_return"]
FORWARD_EXCESS_RETURN_COLUMNS = [
    "date",
    "ticker",
    "horizon",
    "benchmark_ticker",
    "forward_return",
    "benchmark_forward_return",
    "forward_excess_return",
]


def compute_forward_returns(
    prices: pd.DataFrame,
    horizons: list[int] | None = None,
) -> pd.DataFrame:
    """Compute future return labels in long format."""

    resolved_horizons = _resolve_horizons(horizons)
    df = _prepare_prices(prices, "prices")
    frames = []

    for horizon in resolved_horizons:
        horizon_df = df[["date", "ticker"]].copy()
        future_price = df.groupby("ticker", sort=False)["adj_close"].shift(-horizon)
        horizon_df["horizon"] = horizon
        horizon_df["forward_return"] = future_price / df["adj_close"] - 1
        frames.append(horizon_df)

    if not frames:
        return pd.DataFrame(columns=FORWARD_RETURN_COLUMNS)

    return (
        pd.concat(frames, ignore_index=True)
        .loc[:, FORWARD_RETURN_COLUMNS]
        .sort_values(["date", "ticker", "horizon"])
        .reset_index(drop=True)
    )


def compute_forward_excess_returns(
    prices: pd.DataFrame,
    benchmark_prices: pd.DataFrame,
    benchmark_tickers: list[str] | None = None,
    horizons: list[int] | None = None,
) -> pd.DataFrame:
    """Compute forward excess returns versus benchmark tickers."""

    resolved_horizons = _resolve_horizons(horizons)
    resolved_benchmarks = _resolve_benchmark_tickers(benchmark_tickers)
    forward_returns = compute_forward_returns(prices, resolved_horizons)
    benchmark_returns = compute_forward_returns(benchmark_prices, resolved_horizons)
    benchmark_returns = benchmark_returns[
        benchmark_returns["ticker"].isin(resolved_benchmarks)
    ].rename(
        columns={
            "ticker": "benchmark_ticker",
            "forward_return": "benchmark_forward_return",
        }
    )

    expanded = _expand_with_benchmarks(forward_returns, resolved_benchmarks)
    merged = expanded.merge(
        benchmark_returns[
            ["date", "horizon", "benchmark_ticker", "benchmark_forward_return"]
        ],
        on=["date", "horizon", "benchmark_ticker"],
        how="left",
    )
    merged["forward_excess_return"] = (
        merged["forward_return"] - merged["benchmark_forward_return"]
    )

    return (
        merged.loc[:, FORWARD_EXCESS_RETURN_COLUMNS]
        .sort_values(["date", "ticker", "horizon", "benchmark_ticker"])
        .reset_index(drop=True)
    )


def save_forward_returns_csv(df: pd.DataFrame, path: str | Path) -> None:
    """Save forward return labels to CSV."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def _prepare_prices(prices: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    _require_columns(prices, REQUIRED_PRICE_COLUMNS, dataset_name)
    df = prices.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df["adj_close"] = pd.to_numeric(df["adj_close"], errors="coerce")
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


def _expand_with_benchmarks(
    forward_returns: pd.DataFrame,
    benchmark_tickers: list[str],
) -> pd.DataFrame:
    if forward_returns.empty or not benchmark_tickers:
        expanded = forward_returns.copy()
        expanded["benchmark_ticker"] = pd.Series(dtype="string")
        return expanded

    base = forward_returns.copy()
    base["_join_key"] = 1
    benchmarks = pd.DataFrame(
        {"benchmark_ticker": benchmark_tickers, "_join_key": 1}
    )
    return base.merge(benchmarks, on="_join_key").drop(columns=["_join_key"])


def _resolve_horizons(horizons: list[int] | None) -> list[int]:
    resolved = DEFAULT_HORIZONS if horizons is None else horizons

    if any(horizon <= 0 for horizon in resolved):
        raise ValueError("horizons must contain positive integers.")

    return list(dict.fromkeys(int(horizon) for horizon in resolved))


def _resolve_benchmark_tickers(
    benchmark_tickers: list[str] | None,
) -> list[str]:
    resolved = (
        DEFAULT_BENCHMARK_TICKERS if benchmark_tickers is None else benchmark_tickers
    )
    normalized = [
        ticker.strip().upper()
        for ticker in resolved
        if ticker.strip()
    ]
    return list(dict.fromkeys(normalized))


def _require_columns(
    df: pd.DataFrame,
    required_columns: set[str],
    dataset_name: str,
) -> None:
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")
