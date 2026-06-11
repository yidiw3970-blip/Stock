import logging

import numpy as np
import pandas as pd
import pytest

from stock_alpha_lab.models import logistic_outperform_model
from stock_alpha_lab.models.logistic_outperform_model import (
    fit_predict_logistic_walk_forward,
    prepare_outperform_dataset,
)
from stock_alpha_lab.models.walk_forward import make_walk_forward_splits


def make_factor_df() -> pd.DataFrame:
    tickers = ["aaa", "bbb", "ccc", "ddd", "eee"]
    rows = []
    for index, ticker in enumerate(tickers, start=1):
        rows.extend(
            [
                {
                    "date": "2026-01-01",
                    "ticker": ticker,
                    "factor_name": "factor_a",
                    "factor_value": float(index),
                },
                {
                    "date": "2026-01-01",
                    "ticker": ticker,
                    "factor_name": "factor_b",
                    "factor_value": float(index * 10),
                },
            ]
        )
    return pd.DataFrame(rows)


def make_forward_returns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2026-01-01"] * 5,
            "ticker": ["AAA", "BBB", "CCC", "DDD", "EEE"],
            "horizon": [20] * 5,
            "forward_return": [0.01, 0.02, 0.03, 0.04, 0.05],
        }
    )


def make_model_dataset(periods: int = 36) -> pd.DataFrame:
    values = np.arange(periods, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.date_range("2018-01-01", periods=periods, freq="MS"),
            "ticker": ["aaa"] * periods,
            "feature_1": values,
            "feature_2": np.sin(values),
            "outperform_target": [index % 2 for index in range(periods)],
        }
    )


def test_prepare_outperform_dataset_generates_target() -> None:
    dataset = prepare_outperform_dataset(
        make_factor_df(),
        make_forward_returns(),
        factor_names=["factor_a"],
        horizon=20,
        top_quantile=0.80,
    )

    assert "outperform_target" in dataset.columns
    assert set(dataset["outperform_target"]) == {0, 1}


def test_prepare_outperform_dataset_top_quantile_logic() -> None:
    dataset = prepare_outperform_dataset(
        make_factor_df(),
        make_forward_returns(),
        factor_names=["factor_a"],
        horizon=20,
        top_quantile=0.80,
    )

    target_by_ticker = dict(zip(dataset["ticker"], dataset["outperform_target"]))
    assert target_by_ticker["EEE"] == 1
    assert target_by_ticker["DDD"] == 0


def test_prepare_outperform_dataset_only_keeps_requested_factors() -> None:
    dataset = prepare_outperform_dataset(
        make_factor_df(),
        make_forward_returns(),
        factor_names=["factor_a"],
        horizon=20,
    )

    assert "factor_a" in dataset.columns
    assert "factor_b" not in dataset.columns


def test_prepare_outperform_dataset_uppercased_ticker() -> None:
    dataset = prepare_outperform_dataset(
        make_factor_df(),
        make_forward_returns(),
        factor_names=["factor_a"],
        horizon=20,
    )

    assert set(dataset["ticker"]) == {"AAA", "BBB", "CCC", "DDD", "EEE"}


def test_prepare_outperform_dataset_missing_columns_raise_value_error() -> None:
    with pytest.raises(ValueError, match="forward_return"):
        prepare_outperform_dataset(
            make_factor_df(),
            make_forward_returns().drop(columns=["forward_return"]),
            factor_names=["factor_a"],
            horizon=20,
        )


def test_fit_predict_logistic_walk_forward_outputs_probability() -> None:
    predictions = fit_predict_logistic_walk_forward(
        make_model_dataset(),
        feature_cols=["feature_1", "feature_2"],
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert "outperform_probability" in predictions.columns
    assert set(predictions["model_type"]) == {"logistic_outperform"}


def test_logistic_probability_is_between_zero_and_one() -> None:
    predictions = fit_predict_logistic_walk_forward(
        make_model_dataset(),
        feature_cols=["feature_1", "feature_2"],
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert predictions["outperform_probability"].between(0, 1).all()


def test_logistic_one_class_training_split_is_handled(
    caplog: pytest.LogCaptureFixture,
) -> None:
    data = make_model_dataset()
    data["outperform_target"] = 1

    with caplog.at_level(logging.WARNING), pytest.raises(
        ValueError,
        match="No logistic walk-forward predictions",
    ):
        fit_predict_logistic_walk_forward(
            data,
            feature_cols=["feature_1", "feature_2"],
            train_years=1,
            test_months=3,
            min_train_obs=12,
        )

    assert "one class" in caplog.text


def test_logistic_test_rows_do_not_participate_in_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = make_model_dataset()
    splits = make_walk_forward_splits(
        data,
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    class SpyScaler:
        fit_indexes: list[list[int]] = []

        def fit_transform(self, x: pd.DataFrame) -> np.ndarray:
            self.__class__.fit_indexes.append(list(x.index))
            return x.to_numpy(dtype=float)

        def transform(self, x: pd.DataFrame) -> np.ndarray:
            return x.to_numpy(dtype=float)

    monkeypatch.setattr(logistic_outperform_model, "StandardScaler", SpyScaler)

    fit_predict_logistic_walk_forward(
        data,
        feature_cols=["feature_1", "feature_2"],
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    for fit_indexes, split in zip(SpyScaler.fit_indexes, splits, strict=True):
        assert set(fit_indexes).isdisjoint(split["test_index"])


def test_logistic_nan_feature_rows_are_dropped_safely() -> None:
    data = make_model_dataset()
    data.loc[12, "feature_1"] = np.nan

    predictions = fit_predict_logistic_walk_forward(
        data,
        feature_cols=["feature_1", "feature_2"],
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert pd.Timestamp("2019-01-01") not in set(predictions["date"])
