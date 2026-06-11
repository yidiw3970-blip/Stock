"""JACKAL Lens inspired market-tempo hypothesis feature engineering."""

from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_PRICE_FACTOR_COLUMNS = {
    "date",
    "ticker",
    "momentum_20d",
    "volatility_60d",
    "price_vs_ma_50",
    "price_vs_ma_200",
}

BENCHMARK_TICKERS = {
    "SPY": "relative_strength_vs_spy_20d",
    "QQQ": "relative_strength_vs_qqq_20d",
    "SMH": "relative_strength_vs_smh_20d",
}

OUTPUT_COLUMNS = [
    "date",
    "ticker",
    "relative_strength_vs_spy_20d",
    "relative_strength_vs_qqq_20d",
    "relative_strength_vs_smh_20d",
    "trend_filter_50_200",
    "pullback_depth_20d",
    "distance_to_ma50",
    "distance_to_ma200",
    "volatility_risk_bucket",
    "jackal_timing_hypothesis_strength",
    "jackal_missing_reason",
]


def compute_jackal_factors(
    price_factors: pd.DataFrame,
    benchmark_factors: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compute JACKAL Lens inspired candidate timing hypothesis features."""

    _require_columns(price_factors, REQUIRED_PRICE_FACTOR_COLUMNS, "price_factors")
    df = _prepare_price_factors(price_factors)
    output = df[["date", "ticker"]].copy()
    missing_reasons = pd.Series("", index=df.index, dtype="string")

    output = _add_relative_strength_columns(
        output,
        df,
        benchmark_factors,
        missing_reasons,
    )
    output["trend_filter_50_200"] = _compute_trend_filter(df)
    output["pullback_depth_20d"] = -df["momentum_20d"]
    output["distance_to_ma50"] = df["price_vs_ma_50"]
    output["distance_to_ma200"] = df["price_vs_ma_200"]
    output["volatility_risk_bucket"] = df["volatility_60d"].map(
        _volatility_risk_bucket
    )

    missing_reasons = _append_missing_reason(
        missing_reasons,
        output["trend_filter_50_200"].isna(),
        "missing trend inputs",
    )
    missing_reasons = _append_missing_reason(
        missing_reasons,
        df["momentum_20d"].isna(),
        "missing momentum_20d",
    )
    missing_reasons = _append_missing_reason(
        missing_reasons,
        df["volatility_60d"].isna(),
        "missing volatility_60d",
    )

    output["jackal_timing_hypothesis_strength"] = _compute_timing_strength(output)
    output["jackal_missing_reason"] = missing_reasons.fillna("")
    return output.loc[:, OUTPUT_COLUMNS].sort_values(["date", "ticker"]).reset_index(
        drop=True
    )


def _prepare_price_factors(price_factors: pd.DataFrame) -> pd.DataFrame:
    df = price_factors.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()

    for column in REQUIRED_PRICE_FACTOR_COLUMNS - {"date", "ticker"}:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df.sort_values(["date", "ticker"]).reset_index(drop=True)


def _add_relative_strength_columns(
    output: pd.DataFrame,
    df: pd.DataFrame,
    benchmark_factors: pd.DataFrame | None,
    missing_reasons: pd.Series,
) -> pd.DataFrame:
    if benchmark_factors is None:
        for output_column in BENCHMARK_TICKERS.values():
            output[output_column] = np.nan
        _append_missing_reason(
            missing_reasons,
            pd.Series(True, index=df.index),
            "missing benchmark_factors",
        )
        return output

    _require_columns(
        benchmark_factors, REQUIRED_PRICE_FACTOR_COLUMNS, "benchmark_factors"
    )
    benchmarks = _prepare_price_factors(benchmark_factors)

    for benchmark_ticker, output_column in BENCHMARK_TICKERS.items():
        benchmark = benchmarks[benchmarks["ticker"] == benchmark_ticker]
        if benchmark.empty:
            output[output_column] = np.nan
            _append_missing_reason(
                missing_reasons,
                pd.Series(True, index=df.index),
                f"missing {benchmark_ticker} benchmark",
            )
            continue

        benchmark_momentum = benchmark[["date", "momentum_20d"]].rename(
            columns={"momentum_20d": f"{benchmark_ticker}_momentum_20d"}
        )
        merged = df[["date", "momentum_20d"]].merge(
            benchmark_momentum,
            on="date",
            how="left",
        )
        benchmark_column = f"{benchmark_ticker}_momentum_20d"
        output[output_column] = merged["momentum_20d"] - merged[benchmark_column]
        _append_missing_reason(
            missing_reasons,
            output[output_column].isna(),
            f"missing {benchmark_ticker} relative strength",
        )

    return output


def _compute_trend_filter(df: pd.DataFrame) -> pd.Series:
    ma50_above = df["price_vs_ma_50"] > 0
    ma200_above = df["price_vs_ma_200"] > 0
    missing = df["price_vs_ma_50"].isna() | df["price_vs_ma_200"].isna()
    trend = (ma50_above.astype(int) + ma200_above.astype(int)) * 50
    return trend.mask(missing, np.nan)


def _compute_timing_strength(output: pd.DataFrame) -> pd.Series:
    relative_strength = (
        output["relative_strength_vs_smh_20d"]
        .combine_first(output["relative_strength_vs_qqq_20d"])
        .combine_first(output["relative_strength_vs_spy_20d"])
    )
    relative_component = relative_strength.map(_relative_strength_component).fillna(50)
    trend_component = output["trend_filter_50_200"].fillna(50)
    pullback_component = (-output["pullback_depth_20d"]).map(_pullback_component)
    volatility_component = output["volatility_risk_bucket"].map(
        _volatility_component
    )
    strength = (
        0.35 * relative_component
        + 0.35 * trend_component
        + 0.15 * pullback_component
        + 0.15 * volatility_component
    )
    return strength.clip(0, 100).round(2)


def _relative_strength_component(value: float) -> float:
    if pd.isna(value):
        return 50.0
    if value <= -0.10:
        return 0.0
    if value >= 0.10:
        return 100.0
    return float((value + 0.10) / 0.20 * 100)


def _pullback_component(momentum_20d: float) -> float:
    if pd.isna(momentum_20d):
        return 50.0
    if -0.15 <= momentum_20d <= 0.05:
        return 100.0
    if momentum_20d < -0.15:
        return float(np.clip((momentum_20d + 0.30) / 0.15 * 100, 0, 100))
    return float(np.clip((0.20 - momentum_20d) / 0.15 * 100, 0, 100))


def _volatility_risk_bucket(value: float) -> str:
    if pd.isna(value):
        return "unknown"
    if value < 0.25:
        return "low"
    if value < 0.50:
        return "medium"
    return "high"


def _volatility_component(bucket: str) -> float:
    return {
        "low": 100.0,
        "medium": 60.0,
        "high": 20.0,
        "unknown": 50.0,
    }[bucket]


def _append_missing_reason(
    reasons: pd.Series,
    mask: pd.Series,
    reason: str,
) -> pd.Series:
    for index in reasons[mask.fillna(False)].index:
        current = reasons.loc[index]
        reasons.loc[index] = reason if not current else f"{current}; {reason}"
    return reasons


def _require_columns(
    df: pd.DataFrame, required_columns: set[str], dataset_name: str
) -> None:
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")
