from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stock_alpha_lab.research.forward_returns import (
    compute_forward_excess_returns,
    compute_forward_returns,
    save_forward_returns_csv,
)


def make_prices(
    ticker: str = "AAA",
    periods: int = 25,
    start_price: float = 1.0,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=periods, freq="D"),
            "ticker": ticker,
            "adj_close": np.arange(start_price, start_price + periods),
        }
    )


def test_single_ticker_forward_return_20d_calculates_correctly() -> None:
    prices = make_prices(ticker="AAA", periods=25, start_price=1)

    forward_returns = compute_forward_returns(prices, horizons=[20])
    first_row = forward_returns.iloc[0]

    assert first_row["horizon"] == 20
    assert np.isclose(first_row["forward_return"], 21.0 / 1.0 - 1)


def test_multi_ticker_forward_returns_do_not_cross() -> None:
    prices = pd.concat(
        [
            make_prices(ticker="AAA", periods=25, start_price=1),
            make_prices(ticker="BBB", periods=25, start_price=101),
        ],
        ignore_index=True,
    )

    forward_returns = compute_forward_returns(prices, horizons=[20])
    bbb_first = forward_returns[forward_returns["ticker"] == "BBB"].iloc[0]

    assert np.isclose(bbb_first["forward_return"], 121.0 / 101.0 - 1)


def test_insufficient_data_returns_nan() -> None:
    prices = make_prices(periods=10)

    forward_returns = compute_forward_returns(prices, horizons=[20])

    assert forward_returns["forward_return"].isna().all()


def test_output_is_long_format() -> None:
    prices = make_prices(periods=3)

    forward_returns = compute_forward_returns(prices, horizons=[1, 2])

    assert list(forward_returns.columns) == [
        "date",
        "ticker",
        "horizon",
        "forward_return",
    ]
    assert len(forward_returns) == 6


def test_ticker_is_uppercased() -> None:
    prices = make_prices(ticker="aaa", periods=3)

    forward_returns = compute_forward_returns(prices, horizons=[1])

    assert set(forward_returns["ticker"]) == {"AAA"}


def test_missing_adj_close_raises_value_error() -> None:
    prices = make_prices().drop(columns=["adj_close"])

    with pytest.raises(ValueError, match="adj_close"):
        compute_forward_returns(prices)


def test_forward_excess_returns_vs_spy_calculates_correctly() -> None:
    prices = make_prices(ticker="AAA", periods=25, start_price=100)
    benchmark_prices = make_prices(ticker="SPY", periods=25, start_price=200)

    excess_returns = compute_forward_excess_returns(
        prices,
        benchmark_prices,
        benchmark_tickers=["SPY"],
        horizons=[20],
    )
    first_row = excess_returns.iloc[0]

    stock_forward_return = 120.0 / 100.0 - 1
    benchmark_forward_return = 220.0 / 200.0 - 1

    assert np.isclose(first_row["forward_return"], stock_forward_return)
    assert np.isclose(
        first_row["benchmark_forward_return"],
        benchmark_forward_return,
    )
    assert np.isclose(first_row["forward_excess_return"], 0.10)


def test_missing_benchmark_outputs_nan_for_requested_benchmark() -> None:
    prices = make_prices(ticker="AAA", periods=25, start_price=100)
    benchmark_prices = make_prices(ticker="QQQ", periods=25, start_price=200)

    excess_returns = compute_forward_excess_returns(
        prices,
        benchmark_prices,
        benchmark_tickers=["SPY"],
        horizons=[20],
    )

    assert set(excess_returns["benchmark_ticker"]) == {"SPY"}
    assert excess_returns["benchmark_forward_return"].isna().all()
    assert excess_returns["forward_excess_return"].isna().all()


def test_save_forward_returns_csv_writes_file(tmp_path: Path) -> None:
    forward_returns = compute_forward_returns(make_prices(periods=3), horizons=[1])
    output_path = tmp_path / "nested" / "forward_returns.csv"

    save_forward_returns_csv(forward_returns, output_path)
    saved = pd.read_csv(output_path)

    assert output_path.exists()
    assert list(saved.columns) == [
        "date",
        "ticker",
        "horizon",
        "forward_return",
    ]
