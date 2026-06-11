"""Information Coefficient analysis for factor validation."""

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
DAILY_IC_COLUMNS = ["date", "factor_name", "horizon", "ic", "obs_count"]
IC_SUMMARY_COLUMNS = [
    "factor_name",
    "horizon",
    "mean_ic",
    "median_ic",
    "ic_std",
    "ic_hit_rate",
    "ic_t_stat",
    "ic_count",
]


def compute_daily_ic(
    factor_df: pd.DataFrame,
    forward_return_df: pd.DataFrame,
    min_obs: int = 5,
) -> pd.DataFrame:
    """Compute daily cross-sectional Spearman IC by factor and horizon."""

    if min_obs <= 0:
        raise ValueError("min_obs must be a positive integer.")

    factors = _prepare_factor_df(factor_df)
    forward_returns = _prepare_forward_return_df(forward_return_df)
    merged = factors.merge(
        forward_returns,
        on=["date", "ticker"],
        how="inner",
    )

    if merged.empty:
        return pd.DataFrame(columns=DAILY_IC_COLUMNS)

    rows = []
    group_columns = ["date", "factor_name", "horizon"]

    for group_key, group in merged.groupby(group_columns, sort=True):
        date, factor_name, horizon = group_key
        clean = group[["factor_value", "forward_return"]].dropna()
        obs_count = int(len(clean))
        ic = _compute_spearman_ic(clean, min_obs)
        rows.append(
            {
                "date": date,
                "factor_name": factor_name,
                "horizon": horizon,
                "ic": ic,
                "obs_count": obs_count,
            }
        )

    return pd.DataFrame(rows, columns=DAILY_IC_COLUMNS).sort_values(
        ["date", "factor_name", "horizon"]
    ).reset_index(drop=True)


def summarize_ic(daily_ic: pd.DataFrame) -> pd.DataFrame:
    """Summarize daily IC results by factor and horizon."""

    _require_columns(daily_ic, set(DAILY_IC_COLUMNS), "daily_ic")
    df = daily_ic.copy()
    df["horizon"] = pd.to_numeric(df["horizon"], errors="raise").astype("int64")
    df["ic"] = pd.to_numeric(df["ic"], errors="coerce")

    rows = []
    for (factor_name, horizon), group in df.groupby(
        ["factor_name", "horizon"], sort=True
    ):
        ic_values = group["ic"].dropna()
        ic_count = int(len(ic_values))
        mean_ic = ic_values.mean()
        median_ic = ic_values.median()
        ic_std = ic_values.std(ddof=1)
        ic_hit_rate = (ic_values > 0).mean() if ic_count else np.nan
        ic_t_stat = _compute_t_stat(mean_ic, ic_std, ic_count)

        rows.append(
            {
                "factor_name": factor_name,
                "horizon": horizon,
                "mean_ic": mean_ic,
                "median_ic": median_ic,
                "ic_std": ic_std,
                "ic_hit_rate": ic_hit_rate,
                "ic_t_stat": ic_t_stat,
                "ic_count": ic_count,
            }
        )

    return pd.DataFrame(rows, columns=IC_SUMMARY_COLUMNS).sort_values(
        ["factor_name", "horizon"]
    ).reset_index(drop=True)


def run_ic_analysis(
    factor_df: pd.DataFrame,
    forward_return_df: pd.DataFrame,
    min_obs: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run daily IC and IC summary calculations."""

    daily_ic = compute_daily_ic(factor_df, forward_return_df, min_obs=min_obs)
    ic_summary = summarize_ic(daily_ic)
    return daily_ic, ic_summary


def _prepare_factor_df(factor_df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(factor_df, FACTOR_REQUIRED_COLUMNS, "factor_df")
    df = factor_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df["factor_name"] = df["factor_name"].astype("string").str.strip()
    df["factor_value"] = pd.to_numeric(df["factor_value"], errors="coerce")
    return df


def _prepare_forward_return_df(
    forward_return_df: pd.DataFrame,
) -> pd.DataFrame:
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


def _compute_spearman_ic(clean: pd.DataFrame, min_obs: int) -> float:
    if len(clean) < min_obs:
        return np.nan

    if clean["factor_value"].nunique(dropna=True) <= 1:
        return np.nan

    if clean["forward_return"].nunique(dropna=True) <= 1:
        return np.nan

    return float(clean["factor_value"].corr(clean["forward_return"], method="spearman"))


def _compute_t_stat(mean_ic: float, ic_std: float, ic_count: int) -> float:
    if ic_count < 2 or pd.isna(ic_std) or ic_std == 0:
        return np.nan

    return float(mean_ic / (ic_std / np.sqrt(ic_count)))


def _require_columns(
    df: pd.DataFrame,
    required_columns: set[str],
    dataset_name: str,
) -> None:
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")
