import numpy as np
import pandas as pd
import pytest

from stock_alpha_lab.research.ic_analysis import (
    compute_daily_ic,
    run_ic_analysis,
    summarize_ic,
)


def make_factor_df(
    values: list[float],
    date: str = "2026-01-01",
    factor_name: str = "factor_a",
    tickers: list[str] | None = None,
) -> pd.DataFrame:
    resolved_tickers = tickers or [f"T{i}" for i in range(1, len(values) + 1)]
    return pd.DataFrame(
        {
            "date": [date] * len(values),
            "ticker": resolved_tickers,
            "factor_name": [factor_name] * len(values),
            "factor_value": values,
        }
    )


def make_forward_return_df(
    values: list[float],
    date: str = "2026-01-01",
    horizon: int = 20,
    tickers: list[str] | None = None,
) -> pd.DataFrame:
    resolved_tickers = tickers or [f"T{i}" for i in range(1, len(values) + 1)]
    return pd.DataFrame(
        {
            "date": [date] * len(values),
            "ticker": resolved_tickers,
            "horizon": [horizon] * len(values),
            "forward_return": values,
        }
    )


def test_compute_daily_ic_perfect_positive_is_one() -> None:
    daily_ic = compute_daily_ic(
        make_factor_df([1, 2, 3, 4, 5]),
        make_forward_return_df([10, 20, 30, 40, 50]),
        min_obs=5,
    )

    assert np.isclose(daily_ic.loc[0, "ic"], 1.0)


def test_compute_daily_ic_perfect_negative_is_minus_one() -> None:
    daily_ic = compute_daily_ic(
        make_factor_df([1, 2, 3, 4, 5]),
        make_forward_return_df([50, 40, 30, 20, 10]),
        min_obs=5,
    )

    assert np.isclose(daily_ic.loc[0, "ic"], -1.0)


def test_compute_daily_ic_min_obs_returns_nan() -> None:
    daily_ic = compute_daily_ic(
        make_factor_df([1, 2, 3, 4]),
        make_forward_return_df([10, 20, 30, 40]),
        min_obs=5,
    )

    assert pd.isna(daily_ic.loc[0, "ic"])
    assert daily_ic.loc[0, "obs_count"] == 4


def test_compute_daily_ic_constant_factor_returns_nan() -> None:
    daily_ic = compute_daily_ic(
        make_factor_df([1, 1, 1, 1, 1]),
        make_forward_return_df([10, 20, 30, 40, 50]),
        min_obs=5,
    )

    assert pd.isna(daily_ic.loc[0, "ic"])


def test_compute_daily_ic_drops_missing_values_safely() -> None:
    daily_ic = compute_daily_ic(
        make_factor_df([1, 2, np.nan, 4, 5]),
        make_forward_return_df([10, 20, 30, 40, 50]),
        min_obs=4,
    )

    assert np.isclose(daily_ic.loc[0, "ic"], 1.0)
    assert daily_ic.loc[0, "obs_count"] == 4


def test_summarize_ic_calculates_mean_hit_rate_and_count() -> None:
    daily_ic = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
            "factor_name": ["factor_a", "factor_a", "factor_a"],
            "horizon": [20, 20, 20],
            "ic": [0.10, -0.05, 0.15],
            "obs_count": [5, 5, 5],
        }
    )

    summary = summarize_ic(daily_ic)

    assert np.isclose(summary.loc[0, "mean_ic"], np.mean([0.10, -0.05, 0.15]))
    assert np.isclose(summary.loc[0, "ic_hit_rate"], 2 / 3)
    assert summary.loc[0, "ic_count"] == 3


def test_summarize_ic_t_stat_is_nan_when_count_below_two() -> None:
    daily_ic = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01"]),
            "factor_name": ["factor_a"],
            "horizon": [20],
            "ic": [0.10],
            "obs_count": [5],
        }
    )

    summary = summarize_ic(daily_ic)

    assert pd.isna(summary.loc[0, "ic_t_stat"])


def test_multi_factor_and_horizon_do_not_mix() -> None:
    factor_df = pd.concat(
        [
            make_factor_df([1, 2, 3, 4, 5], factor_name="factor_a"),
            make_factor_df([5, 4, 3, 2, 1], factor_name="factor_b"),
        ],
        ignore_index=True,
    )
    forward_return_df = pd.concat(
        [
            make_forward_return_df([10, 20, 30, 40, 50], horizon=20),
            make_forward_return_df([50, 40, 30, 20, 10], horizon=60),
        ],
        ignore_index=True,
    )

    daily_ic, summary = run_ic_analysis(factor_df, forward_return_df, min_obs=5)

    assert len(daily_ic) == 4
    assert len(summary) == 4
    assert set(daily_ic["factor_name"]) == {"factor_a", "factor_b"}
    assert set(daily_ic["horizon"]) == {20, 60}


def test_missing_required_factor_column_raises_value_error() -> None:
    factor_df = make_factor_df([1, 2, 3, 4, 5]).drop(columns=["factor_value"])
    forward_return_df = make_forward_return_df([10, 20, 30, 40, 50])

    with pytest.raises(ValueError, match="factor_value"):
        compute_daily_ic(factor_df, forward_return_df)


def test_ticker_is_uppercased_before_merge() -> None:
    factor_df = make_factor_df([1, 2, 3, 4, 5], tickers=["a", "b", "c", "d", "e"])
    forward_return_df = make_forward_return_df(
        [10, 20, 30, 40, 50],
        tickers=["A", "B", "C", "D", "E"],
    )

    daily_ic = compute_daily_ic(factor_df, forward_return_df, min_obs=5)

    assert np.isclose(daily_ic.loc[0, "ic"], 1.0)
