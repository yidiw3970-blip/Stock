from pathlib import Path

import pandas as pd
import pytest

from scripts.update_prices import parse_args, parse_tickers
from stock_alpha_lab.data_sources import yfinance_client
from stock_alpha_lab.data_sources.yfinance_client import (
    download_price_history,
    normalize_yfinance_history,
    save_prices_csv,
)


def sample_history(include_adj_close: bool = True) -> pd.DataFrame:
    data = {
        "Open": [10.0, 11.0],
        "High": [12.0, 13.0],
        "Low": [9.5, 10.5],
        "Close": [11.5, 12.5],
        "Volume": [1000, 1200],
    }

    if include_adj_close:
        data["Adj Close"] = [11.0, 12.0]

    return pd.DataFrame(
        data,
        index=pd.DatetimeIndex(
            ["2024-01-02 09:30:00-05:00", "2024-01-03 09:30:00-05:00"],
            name="Date",
        ),
    )


def test_normalize_yfinance_history_maps_adj_close() -> None:
    df = normalize_yfinance_history(sample_history(include_adj_close=True), "nvda")

    assert list(df.columns) == [
        "date",
        "ticker",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
    ]
    assert list(df["adj_close"]) == [11.0, 12.0]


def test_normalize_yfinance_history_uses_close_when_adj_close_missing() -> None:
    df = normalize_yfinance_history(sample_history(include_adj_close=False), "NVDA")

    assert list(df["adj_close"]) == [11.5, 12.5]


def test_normalize_yfinance_history_uppercases_ticker() -> None:
    df = normalize_yfinance_history(sample_history(), "nvda")

    assert set(df["ticker"]) == {"NVDA"}


def test_normalize_yfinance_history_removes_date_timezone() -> None:
    df = normalize_yfinance_history(sample_history(), "NVDA")

    assert df["date"].dt.tz is None


def test_normalize_yfinance_history_missing_core_column_raises() -> None:
    raw_df = sample_history().drop(columns=["Volume"])

    with pytest.raises(ValueError, match="volume"):
        normalize_yfinance_history(raw_df, "NVDA")


def test_download_price_history_continues_after_ticker_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_download(
        ticker: str,
        start: str,
        end: str | None,
        auto_adjust: bool,
        progress: bool,
        threads: bool,
    ) -> pd.DataFrame:
        assert start == "2020-01-01"
        assert end is None
        assert auto_adjust is False
        assert progress is False
        assert threads is False

        if ticker == "BAD":
            raise RuntimeError("simulated failure")
        return sample_history()

    monkeypatch.setattr(yfinance_client.yf, "download", fake_download)
    monkeypatch.setattr(yfinance_client.time, "sleep", lambda seconds: None)

    df = download_price_history(
        ["good", "bad"], start="2020-01-01", sleep_seconds=0
    )

    assert set(df["ticker"]) == {"GOOD"}


def test_download_price_history_retries_rate_limit_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    sleeps: list[float] = []

    def fake_download(
        ticker: str,
        start: str,
        end: str | None,
        auto_adjust: bool,
        progress: bool,
        threads: bool,
    ) -> pd.DataFrame:
        calls.append(ticker)
        if len(calls) == 1:
            raise RuntimeError("YFRateLimitError: Too Many Requests. Rate limited.")
        return sample_history()

    monkeypatch.setattr(yfinance_client.yf, "download", fake_download)
    monkeypatch.setattr(
        yfinance_client.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    df = download_price_history(
        ["nvda"], start="2024-01-01", sleep_seconds=5, max_retries=2
    )

    assert calls == ["NVDA", "NVDA"]
    assert sleeps == [5]
    assert set(df["ticker"]) == {"NVDA"}


def test_download_price_history_raises_when_all_tickers_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_download(
        ticker: str,
        start: str,
        end: str | None,
        auto_adjust: bool,
        progress: bool,
        threads: bool,
    ) -> pd.DataFrame:
        raise RuntimeError(f"simulated failure for {ticker}")

    monkeypatch.setattr(yfinance_client.yf, "download", fake_download)
    monkeypatch.setattr(yfinance_client.time, "sleep", lambda seconds: None)

    with pytest.raises(RuntimeError, match="rate limit.*reduce the number"):
        download_price_history(["bad"], start="2020-01-01", sleep_seconds=0)


def test_save_prices_csv_writes_file(tmp_path: Path) -> None:
    df = normalize_yfinance_history(sample_history(), "NVDA")
    output_path = tmp_path / "nested" / "prices.csv"

    save_prices_csv(df, output_path)

    saved = pd.read_csv(output_path)

    assert output_path.exists()
    assert list(saved.columns) == [
        "date",
        "ticker",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
    ]


def test_parse_tickers_uppercases_comma_separated_values() -> None:
    assert parse_tickers("nvda, MU,") == ["NVDA", "MU"]


def test_parse_args_accepts_tickers_and_rate_limit_options() -> None:
    args = parse_args(
        [
            "--tickers",
            "NVDA,MU",
            "--start",
            "2024-01-01",
            "--sleep-seconds",
            "5",
            "--max-retries",
            "3",
        ]
    )

    assert args.tickers == "NVDA,MU"
    assert args.start == "2024-01-01"
    assert args.sleep_seconds == 5
    assert args.max_retries == 3
