import numpy as np
import pandas as pd
import pytest

from stock_alpha_lab.factors.price_factors import compute_price_factors


def make_prices(
    ticker: str = "NVDA",
    periods: int = 260,
    price_offset: float = 0.0,
    volume: int = 10,
) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    prices = np.arange(1, periods + 1, dtype=float) + price_offset

    return pd.DataFrame(
        {
            "date": dates,
            "ticker": ticker,
            "adj_close": prices,
            "volume": volume,
        }
    )


def test_momentum_20d_calculates_correctly() -> None:
    factors = compute_price_factors(make_prices(periods=30))

    expected = 21.0 / 1.0 - 1

    assert np.isclose(factors.loc[20, "momentum_20d"], expected)


def test_ma_50_calculates_correctly() -> None:
    factors = compute_price_factors(make_prices(periods=60))

    expected = np.mean(np.arange(1, 51, dtype=float))

    assert np.isclose(factors.loc[49, "ma_50"], expected)


def test_rolling_high_and_low_252d_calculate_correctly() -> None:
    factors = compute_price_factors(make_prices(periods=260))
    last_row = factors.iloc[-1]

    assert last_row["rolling_high_252d"] == 260.0
    assert last_row["rolling_low_252d"] == 9.0


def test_distance_to_52w_high_and_low_calculate_correctly() -> None:
    factors = compute_price_factors(make_prices(periods=260))
    last_row = factors.iloc[-1]

    assert last_row["distance_to_52w_high"] == 0.0
    assert np.isclose(last_row["distance_to_52w_low"], 260.0 / 9.0 - 1)


def test_avg_dollar_volume_60d_calculates_correctly() -> None:
    factors = compute_price_factors(make_prices(periods=80, volume=10))

    expected = np.mean(np.arange(21, 81, dtype=float) * 10)

    assert np.isclose(factors.iloc[-1]["avg_dollar_volume_60d"], expected)


def test_multi_ticker_data_does_not_cross_between_groups() -> None:
    prices = pd.concat(
        [
            make_prices(ticker="AAA", periods=25),
            make_prices(ticker="BBB", periods=25, price_offset=1000),
        ],
        ignore_index=True,
    )

    factors = compute_price_factors(prices)
    bbb_factors = factors[factors["ticker"] == "BBB"].reset_index(drop=True)
    expected = 1021.0 / 1001.0 - 1

    assert np.isclose(bbb_factors.loc[20, "momentum_20d"], expected)


def test_insufficient_data_returns_nan() -> None:
    factors = compute_price_factors(make_prices(periods=20))

    assert pd.isna(factors.loc[19, "momentum_20d"])
    assert pd.isna(factors.loc[19, "ma_50"])
    assert pd.isna(factors.loc[19, "rolling_high_252d"])


def test_missing_adj_close_raises_value_error() -> None:
    prices = make_prices().drop(columns=["adj_close"])

    with pytest.raises(ValueError, match="adj_close"):
        compute_price_factors(prices)


def test_ticker_is_uppercased() -> None:
    factors = compute_price_factors(make_prices(ticker="nvda", periods=5))

    assert set(factors["ticker"]) == {"NVDA"}
