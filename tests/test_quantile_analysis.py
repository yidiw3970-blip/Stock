import numpy as np
import pandas as pd
import pytest

from stock_alpha_lab.research.quantile_analysis import (
    assign_factor_quantiles,
    compute_quantile_returns,
    compute_quantile_spread,
    run_quantile_analysis,
    summarize_quantile_analysis,
)


def make_factor_df(
    factor_name: str = "factor_a",
    date: str = "2026-01-01",
    values: list[float] | None = None,
    tickers: list[str] | None = None,
) -> pd.DataFrame:
    resolved_values = values or list(range(1, 11))
    resolved_tickers = tickers or [
        f"T{i}" for i in range(1, len(resolved_values) + 1)
    ]
    return pd.DataFrame(
        {
            "date": [date] * len(resolved_values),
            "ticker": resolved_tickers,
            "factor_name": [factor_name] * len(resolved_values),
            "factor_value": resolved_values,
        }
    )


def make_forward_returns(
    date: str = "2026-01-01",
    horizon: int = 20,
    values: list[float] | None = None,
    tickers: list[str] | None = None,
) -> pd.DataFrame:
    resolved_values = values or [0.01 * i for i in range(1, 11)]
    resolved_tickers = tickers or [
        f"T{i}" for i in range(1, len(resolved_values) + 1)
    ]
    return pd.DataFrame(
        {
            "date": [date] * len(resolved_values),
            "ticker": resolved_tickers,
            "horizon": [horizon] * len(resolved_values),
            "forward_return": resolved_values,
        }
    )


def test_assign_factor_quantiles_splits_into_five_groups() -> None:
    quantiles = assign_factor_quantiles(
        make_factor_df(),
        n_quantiles=5,
        min_obs=10,
    )

    assert set(quantiles["quantile"].dropna()) == {1, 2, 3, 4, 5}
    assert quantiles["quantile"].value_counts().sort_index().tolist() == [
        2,
        2,
        2,
        2,
        2,
    ]


def test_highest_factor_value_is_highest_quantile() -> None:
    quantiles = assign_factor_quantiles(
        make_factor_df(),
        n_quantiles=5,
        min_obs=10,
    )
    highest = quantiles.loc[quantiles["factor_value"].idxmax()]

    assert highest["quantile"] == 5


def test_min_obs_returns_nan_quantiles() -> None:
    quantiles = assign_factor_quantiles(
        make_factor_df(values=[1, 2, 3, 4]),
        n_quantiles=5,
        min_obs=10,
    )

    assert quantiles["quantile"].isna().all()


def test_constant_factor_returns_nan_quantiles() -> None:
    quantiles = assign_factor_quantiles(
        make_factor_df(values=[1] * 10),
        n_quantiles=5,
        min_obs=10,
    )

    assert quantiles["quantile"].isna().all()


def test_duplicate_values_do_not_crash_quantile_assignment() -> None:
    quantiles = assign_factor_quantiles(
        make_factor_df(values=[1, 1, 2, 2, 3, 3, 4, 4, 5, 5]),
        n_quantiles=5,
        min_obs=10,
    )

    assert quantiles["quantile"].notna().all()


def test_compute_quantile_returns_calculates_group_stats() -> None:
    factor_quantiles = assign_factor_quantiles(
        make_factor_df(),
        n_quantiles=5,
        min_obs=10,
    )
    forward_returns = make_forward_returns()

    quantile_returns = compute_quantile_returns(factor_quantiles, forward_returns)
    top = quantile_returns[quantile_returns["quantile"] == 5].iloc[0]

    assert np.isclose(top["mean_return"], np.mean([0.09, 0.10]))
    assert np.isclose(top["median_return"], np.median([0.09, 0.10]))
    assert top["hit_rate"] == 1.0
    assert top["count"] == 2


def test_compute_quantile_spread_calculates_top_minus_bottom() -> None:
    factor_quantiles = assign_factor_quantiles(
        make_factor_df(),
        n_quantiles=5,
        min_obs=10,
    )
    quantile_returns = compute_quantile_returns(
        factor_quantiles,
        make_forward_returns(),
    )

    spread = compute_quantile_spread(quantile_returns, n_quantiles=5)

    assert np.isclose(spread.loc[0, "top_return"], np.mean([0.09, 0.10]))
    assert np.isclose(spread.loc[0, "bottom_return"], np.mean([0.01, 0.02]))
    assert np.isclose(spread.loc[0, "spread"], 0.08)


def test_compute_quantile_spread_missing_top_returns_nan() -> None:
    quantile_returns = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01"]),
            "factor_name": ["factor_a"],
            "horizon": [20],
            "quantile": [1],
            "mean_return": [0.01],
            "median_return": [0.01],
            "hit_rate": [1.0],
            "count": [2],
        }
    )

    spread = compute_quantile_spread(quantile_returns, n_quantiles=5)

    assert pd.isna(spread.loc[0, "top_return"])
    assert pd.isna(spread.loc[0, "spread"])


def test_summarize_quantile_analysis_calculates_summary_stats() -> None:
    quantile_returns = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02"] * 5),
            "factor_name": ["factor_a"] * 10,
            "horizon": [20] * 10,
            "quantile": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
            "mean_return": [
                0.01,
                0.02,
                0.02,
                0.03,
                0.03,
                0.04,
                0.04,
                0.05,
                0.06,
                0.07,
            ],
            "median_return": [0.0] * 10,
            "hit_rate": [1.0] * 10,
            "count": [2] * 10,
        }
    )
    spread = compute_quantile_spread(quantile_returns, n_quantiles=5)

    summary = summarize_quantile_analysis(quantile_returns, spread)

    assert np.isclose(summary.loc[0, "mean_spread"], 0.05)
    assert summary.loc[0, "spread_hit_rate"] == 1.0
    assert summary.loc[0, "period_count"] == 2
    assert summary.loc[0, "monotonic_share"] == 1.0


def test_multi_factor_multi_horizon_do_not_mix() -> None:
    factor_df = pd.concat(
        [
            make_factor_df(factor_name="factor_a"),
            make_factor_df(factor_name="factor_b"),
        ],
        ignore_index=True,
    )
    forward_returns = pd.concat(
        [
            make_forward_returns(horizon=20),
            make_forward_returns(horizon=60),
        ],
        ignore_index=True,
    )

    _, quantile_returns, spread, summary = run_quantile_analysis(
        factor_df,
        forward_returns,
        n_quantiles=5,
        min_obs=10,
    )

    assert len(quantile_returns.groupby(["factor_name", "horizon"])) == 4
    assert len(spread) == 4
    assert len(summary) == 4


def test_missing_required_factor_column_raises_value_error() -> None:
    factor_df = make_factor_df().drop(columns=["factor_value"])

    with pytest.raises(ValueError, match="factor_value"):
        assign_factor_quantiles(factor_df)


def test_ticker_is_uppercased() -> None:
    quantiles = assign_factor_quantiles(
        make_factor_df(tickers=[f"t{i}" for i in range(1, 11)]),
        n_quantiles=5,
        min_obs=10,
    )

    assert set(quantiles["ticker"]) == {f"T{i}" for i in range(1, 11)}
