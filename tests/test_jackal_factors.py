import numpy as np
import pandas as pd
import pytest

from stock_alpha_lab.factors.jackal_factors import compute_jackal_factors


def price_factor_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2026-01-01",
                    "2026-01-01",
                    "2026-01-02",
                    "2026-01-02",
                ]
            ),
            "ticker": ["AAA", "BBB", "AAA", "BBB"],
            "momentum_20d": [0.08, -0.02, 0.04, 0.12],
            "volatility_60d": [0.10, 0.30, 0.60, np.nan],
            "price_vs_ma_50": [0.02, 0.03, -0.01, -0.02],
            "price_vs_ma_200": [0.05, -0.04, -0.03, 0.01],
        }
    )


def benchmark_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2026-01-01",
                    "2026-01-01",
                    "2026-01-01",
                    "2026-01-02",
                    "2026-01-02",
                    "2026-01-02",
                ]
            ),
            "ticker": ["SPY", "QQQ", "SMH", "SPY", "QQQ", "SMH"],
            "momentum_20d": [0.03, 0.04, 0.05, 0.01, 0.02, 0.03],
            "volatility_60d": [0.10] * 6,
            "price_vs_ma_50": [0.01] * 6,
            "price_vs_ma_200": [0.01] * 6,
        }
    )


def select_factor_row(
    factors: pd.DataFrame,
    date: str,
    ticker: str,
) -> pd.DataFrame:
    return factors[
        (factors["date"] == date)
        & (factors["ticker"] == ticker)
    ]


def test_relative_strength_vs_spy_20d_calculates_correctly() -> None:
    factors = compute_jackal_factors(price_factor_rows(), benchmark_rows())
    row = select_factor_row(factors, "2026-01-01", "AAA")

    assert np.isclose(row.iloc[0]["relative_strength_vs_spy_20d"], 0.05)


def test_missing_benchmark_outputs_nan_and_missing_reason() -> None:
    factors = compute_jackal_factors(price_factor_rows(), benchmark_factors=None)

    assert factors["relative_strength_vs_spy_20d"].isna().all()
    assert factors["jackal_missing_reason"].str.contains(
        "missing benchmark_factors"
    ).all()


def test_trend_filter_three_states() -> None:
    factors = compute_jackal_factors(price_factor_rows(), benchmark_rows())

    aaa_day_1 = select_factor_row(factors, "2026-01-01", "AAA")
    bbb_day_1 = select_factor_row(factors, "2026-01-01", "BBB")
    aaa_day_2 = select_factor_row(factors, "2026-01-02", "AAA")

    assert aaa_day_1.iloc[0]["trend_filter_50_200"] == 100
    assert bbb_day_1.iloc[0]["trend_filter_50_200"] == 50
    assert aaa_day_2.iloc[0]["trend_filter_50_200"] == 0


def test_volatility_risk_bucket_classifies_correctly() -> None:
    factors = compute_jackal_factors(price_factor_rows(), benchmark_rows())

    assert list(factors["volatility_risk_bucket"]) == [
        "low",
        "medium",
        "high",
        "unknown",
    ]


def test_jackal_timing_hypothesis_strength_is_between_0_and_100() -> None:
    factors = compute_jackal_factors(price_factor_rows(), benchmark_rows())

    assert factors["jackal_timing_hypothesis_strength"].between(0, 100).all()


def test_multi_ticker_multi_date_data_does_not_cross() -> None:
    factors = compute_jackal_factors(price_factor_rows(), benchmark_rows())
    aaa_day_2 = select_factor_row(factors, "2026-01-02", "AAA")
    bbb_day_2 = select_factor_row(factors, "2026-01-02", "BBB")

    assert np.isclose(aaa_day_2.iloc[0]["relative_strength_vs_spy_20d"], 0.03)
    assert np.isclose(bbb_day_2.iloc[0]["relative_strength_vs_spy_20d"], 0.11)


def test_missing_required_price_factor_column_raises_value_error() -> None:
    price_factors = price_factor_rows().drop(columns=["momentum_20d"])

    with pytest.raises(ValueError, match="momentum_20d"):
        compute_jackal_factors(price_factors, benchmark_rows())
