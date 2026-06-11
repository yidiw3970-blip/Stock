"""Quantile return analysis for factor validation."""

from __future__ import annotations

import numpy as np
import pandas as pd

FACTOR_REQUIRED_COLUMNS = {"date", "ticker", "factor_name", "factor_value"}
FORWARD_RETURN_REQUIRED_COLUMNS = {
    "date",
    "ticker",
    "horizon",
    "forward_return",
}
FACTOR_QUANTILE_COLUMNS = [
    "date",
    "ticker",
    "factor_name",
    "factor_value",
    "quantile",
]
QUANTILE_RETURN_COLUMNS = [
    "date",
    "factor_name",
    "horizon",
    "quantile",
    "mean_return",
    "median_return",
    "hit_rate",
    "count",
]
QUANTILE_SPREAD_COLUMNS = [
    "date",
    "factor_name",
    "horizon",
    "top_quantile",
    "bottom_quantile",
    "top_return",
    "bottom_return",
    "spread",
]
QUANTILE_SUMMARY_COLUMNS = [
    "factor_name",
    "horizon",
    "mean_top_return",
    "mean_bottom_return",
    "mean_spread",
    "spread_hit_rate",
    "spread_t_stat",
    "period_count",
    "monotonic_share",
]


def assign_factor_quantiles(
    factor_df: pd.DataFrame,
    n_quantiles: int = 5,
    min_obs: int = 10,
) -> pd.DataFrame:
    """Assign cross-sectional factor quantiles by date and factor name."""

    _validate_quantile_params(n_quantiles=n_quantiles, min_obs=min_obs)
    df = _prepare_factor_df(factor_df)
    df["quantile"] = np.nan

    group_columns = ["date", "factor_name"]
    for _, group in df.groupby(group_columns, sort=False):
        quantiles = _assign_group_quantiles(
            group["factor_value"],
            n_quantiles=n_quantiles,
            min_obs=min_obs,
        )
        df.loc[group.index, "quantile"] = quantiles

    return df.loc[:, FACTOR_QUANTILE_COLUMNS].sort_values(
        ["date", "factor_name", "ticker"]
    ).reset_index(drop=True)


def compute_quantile_returns(
    factor_quantiles: pd.DataFrame,
    forward_return_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute forward returns by date, factor, horizon, and quantile."""

    quantiles = _prepare_factor_quantiles(factor_quantiles)
    forward_returns = _prepare_forward_return_df(forward_return_df)
    merged = quantiles.merge(
        forward_returns,
        on=["date", "ticker"],
        how="inner",
    )
    merged = merged.dropna(subset=["quantile"])

    if merged.empty:
        return pd.DataFrame(columns=QUANTILE_RETURN_COLUMNS)

    rows = []
    group_columns = ["date", "factor_name", "horizon", "quantile"]
    for group_key, group in merged.groupby(group_columns, sort=True):
        date, factor_name, horizon, quantile = group_key
        returns = group["forward_return"].dropna()
        count = int(len(returns))
        rows.append(
            {
                "date": date,
                "factor_name": factor_name,
                "horizon": horizon,
                "quantile": quantile,
                "mean_return": returns.mean(),
                "median_return": returns.median(),
                "hit_rate": (returns > 0).mean() if count else np.nan,
                "count": count,
            }
        )

    return pd.DataFrame(rows, columns=QUANTILE_RETURN_COLUMNS).sort_values(
        ["date", "factor_name", "horizon", "quantile"]
    ).reset_index(drop=True)


def compute_quantile_spread(
    quantile_returns: pd.DataFrame,
    n_quantiles: int = 5,
) -> pd.DataFrame:
    """Compute top-minus-bottom quantile spread by date, factor, and horizon."""

    if n_quantiles < 2:
        raise ValueError("n_quantiles must be at least 2.")

    returns = _prepare_quantile_returns(quantile_returns)
    group_columns = ["date", "factor_name", "horizon"]
    base = returns.loc[:, group_columns].drop_duplicates()
    top = _select_quantile_return(returns, quantile=n_quantiles, name="top_return")
    bottom = _select_quantile_return(returns, quantile=1, name="bottom_return")

    spread = base.merge(top, on=group_columns, how="left").merge(
        bottom,
        on=group_columns,
        how="left",
    )
    spread["top_quantile"] = n_quantiles
    spread["bottom_quantile"] = 1
    spread["spread"] = spread["top_return"] - spread["bottom_return"]
    return (
        spread.loc[:, QUANTILE_SPREAD_COLUMNS]
        .sort_values(group_columns)
        .reset_index(drop=True)
    )


def summarize_quantile_analysis(
    quantile_returns: pd.DataFrame,
    quantile_spread: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize quantile return and spread diagnostics."""

    returns = _prepare_quantile_returns(quantile_returns)
    spreads = _prepare_quantile_spread(quantile_spread)
    monotonic = _compute_monotonic_share(returns)
    rows = []

    for (factor_name, horizon), group in spreads.groupby(
        ["factor_name", "horizon"], sort=True
    ):
        valid_spreads = group["spread"].dropna()
        period_count = int(len(valid_spreads))
        mean_spread = valid_spreads.mean()
        spread_std = valid_spreads.std(ddof=1)
        rows.append(
            {
                "factor_name": factor_name,
                "horizon": horizon,
                "mean_top_return": group["top_return"].mean(),
                "mean_bottom_return": group["bottom_return"].mean(),
                "mean_spread": mean_spread,
                "spread_hit_rate": (valid_spreads > 0).mean()
                if period_count
                else np.nan,
                "spread_t_stat": _compute_t_stat(
                    mean_spread,
                    spread_std,
                    period_count,
                ),
                "period_count": period_count,
                "monotonic_share": monotonic.get((factor_name, horizon), np.nan),
            }
        )

    return pd.DataFrame(rows, columns=QUANTILE_SUMMARY_COLUMNS).sort_values(
        ["factor_name", "horizon"]
    ).reset_index(drop=True)


def run_quantile_analysis(
    factor_df: pd.DataFrame,
    forward_return_df: pd.DataFrame,
    n_quantiles: int = 5,
    min_obs: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run quantile assignment, returns, spread, and summary analysis."""

    factor_quantiles = assign_factor_quantiles(
        factor_df,
        n_quantiles=n_quantiles,
        min_obs=min_obs,
    )
    quantile_returns = compute_quantile_returns(factor_quantiles, forward_return_df)
    quantile_spread = compute_quantile_spread(
        quantile_returns,
        n_quantiles=n_quantiles,
    )
    quantile_summary = summarize_quantile_analysis(
        quantile_returns,
        quantile_spread,
    )
    return factor_quantiles, quantile_returns, quantile_spread, quantile_summary


def _assign_group_quantiles(
    values: pd.Series,
    n_quantiles: int,
    min_obs: int,
) -> pd.Series:
    quantiles = pd.Series(np.nan, index=values.index, dtype="float64")
    valid_values = values.dropna()

    if len(valid_values) < min_obs or valid_values.nunique(dropna=True) <= 1:
        return quantiles

    ranks = valid_values.rank(method="first")

    try:
        assigned = pd.qcut(ranks, q=n_quantiles, labels=False) + 1
    except ValueError:
        return quantiles

    quantiles.loc[assigned.index] = assigned.astype("float64")
    return quantiles


def _prepare_factor_df(factor_df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(factor_df, FACTOR_REQUIRED_COLUMNS, "factor_df")
    df = factor_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df["factor_name"] = df["factor_name"].astype("string").str.strip()
    df["factor_value"] = pd.to_numeric(df["factor_value"], errors="coerce")
    return df.sort_values(["date", "factor_name", "ticker"]).reset_index(drop=True)


def _prepare_factor_quantiles(factor_quantiles: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        factor_quantiles,
        set(FACTOR_QUANTILE_COLUMNS),
        "factor_quantiles",
    )
    df = factor_quantiles.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df["factor_name"] = df["factor_name"].astype("string").str.strip()
    df["factor_value"] = pd.to_numeric(df["factor_value"], errors="coerce")
    df["quantile"] = pd.to_numeric(df["quantile"], errors="coerce")
    return df


def _prepare_forward_return_df(forward_return_df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        forward_return_df,
        FORWARD_RETURN_REQUIRED_COLUMNS,
        "forward_return_df",
    )
    df = forward_return_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df["horizon"] = pd.to_numeric(df["horizon"], errors="raise").astype("int64")
    df["forward_return"] = pd.to_numeric(df["forward_return"], errors="coerce")
    return df


def _prepare_quantile_returns(quantile_returns: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        quantile_returns,
        set(QUANTILE_RETURN_COLUMNS),
        "quantile_returns",
    )
    df = quantile_returns.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["factor_name"] = df["factor_name"].astype("string").str.strip()
    df["horizon"] = pd.to_numeric(df["horizon"], errors="raise").astype("int64")
    df["quantile"] = pd.to_numeric(df["quantile"], errors="coerce")
    df["mean_return"] = pd.to_numeric(df["mean_return"], errors="coerce")
    df["median_return"] = pd.to_numeric(df["median_return"], errors="coerce")
    df["hit_rate"] = pd.to_numeric(df["hit_rate"], errors="coerce")
    df["count"] = pd.to_numeric(df["count"], errors="coerce").astype("int64")
    return df


def _prepare_quantile_spread(quantile_spread: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        quantile_spread,
        set(QUANTILE_SPREAD_COLUMNS),
        "quantile_spread",
    )
    df = quantile_spread.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["factor_name"] = df["factor_name"].astype("string").str.strip()
    df["horizon"] = pd.to_numeric(df["horizon"], errors="raise").astype("int64")
    for column in ["top_return", "bottom_return", "spread"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _select_quantile_return(
    quantile_returns: pd.DataFrame,
    quantile: int,
    name: str,
) -> pd.DataFrame:
    columns = ["date", "factor_name", "horizon", "mean_return"]
    return quantile_returns[quantile_returns["quantile"] == quantile].loc[
        :,
        columns,
    ].rename(columns={"mean_return": name})


def _compute_monotonic_share(
    quantile_returns: pd.DataFrame,
) -> dict[tuple[str, int], float]:
    result: dict[tuple[str, int], float] = {}

    for key, group in quantile_returns.groupby(["factor_name", "horizon"], sort=True):
        checks = []
        for _, date_group in group.groupby("date", sort=True):
            returns = (
                date_group.sort_values("quantile")["mean_return"]
                .dropna()
                .to_numpy()
            )
            if len(returns) < 2:
                continue
            checks.append(bool(np.all(np.diff(returns) >= 0)))

        result[key] = float(np.mean(checks)) if checks else np.nan

    return result


def _compute_t_stat(mean_value: float, std_value: float, count: int) -> float:
    if count < 2 or pd.isna(std_value) or std_value == 0:
        return np.nan
    return float(mean_value / (std_value / np.sqrt(count)))


def _validate_quantile_params(n_quantiles: int, min_obs: int) -> None:
    if n_quantiles < 2:
        raise ValueError("n_quantiles must be at least 2.")
    if min_obs <= 0:
        raise ValueError("min_obs must be a positive integer.")


def _require_columns(
    df: pd.DataFrame,
    required_columns: set[str],
    dataset_name: str,
) -> None:
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")
