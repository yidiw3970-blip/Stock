import numpy as np
import pandas as pd
import pytest

from stock_alpha_lab.models import ridge_model
from stock_alpha_lab.models.ridge_model import (
    fit_predict_ridge_walk_forward,
    prepare_regression_dataset,
)
from stock_alpha_lab.models.walk_forward import make_walk_forward_splits


def make_factor_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2026-01-01"] * 6,
            "ticker": ["aaa", "aaa", "aaa", "bbb", "bbb", "bbb"],
            "factor_name": [
                "factor_a",
                "factor_b",
                "unused_factor",
                "factor_a",
                "factor_b",
                "unused_factor",
            ],
            "factor_value": [1.0, 10.0, 100.0, 2.0, 20.0, 200.0],
        }
    )


def make_forward_returns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "ticker": ["AAA", "BBB", "CCC"],
            "horizon": [20, 20, 20],
            "forward_return": [0.05, -0.01, 0.02],
        }
    )


def make_model_dataset(periods: int = 36) -> pd.DataFrame:
    values = np.arange(periods, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.date_range("2018-01-01", periods=periods, freq="MS"),
            "ticker": ["aaa"] * periods,
            "feature_1": values,
            "feature_2": values * 0.5,
            "target_return": values / 100,
        }
    )


def test_prepare_regression_dataset_pivots_factor_long_to_wide() -> None:
    dataset = prepare_regression_dataset(
        make_factor_df(),
        make_forward_returns(),
        factor_names=["factor_a", "factor_b"],
        horizon=20,
    )

    assert {"factor_a", "factor_b"}.issubset(dataset.columns)
    assert dataset.loc[dataset["ticker"] == "AAA", "factor_a"].iloc[0] == 1.0
    assert dataset.loc[dataset["ticker"] == "AAA", "factor_b"].iloc[0] == 10.0


def test_prepare_regression_dataset_only_keeps_requested_factors() -> None:
    dataset = prepare_regression_dataset(
        make_factor_df(),
        make_forward_returns(),
        factor_names=["factor_a"],
        horizon=20,
    )

    assert "factor_a" in dataset.columns
    assert "factor_b" not in dataset.columns
    assert "unused_factor" not in dataset.columns


def test_prepare_regression_dataset_merges_target_return() -> None:
    dataset = prepare_regression_dataset(
        make_factor_df(),
        make_forward_returns(),
        factor_names=["factor_a"],
        horizon=20,
    )

    assert dataset.loc[dataset["ticker"] == "AAA", "target_return"].iloc[0] == 0.05
    assert dataset.loc[dataset["ticker"] == "BBB", "target_return"].iloc[0] == -0.01


def test_prepare_regression_dataset_uppercased_ticker() -> None:
    dataset = prepare_regression_dataset(
        make_factor_df(),
        make_forward_returns(),
        factor_names=["factor_a"],
        horizon=20,
    )

    assert set(dataset["ticker"]) == {"AAA", "BBB"}


def test_prepare_regression_dataset_missing_columns_raise_value_error() -> None:
    with pytest.raises(ValueError, match="factor_value"):
        prepare_regression_dataset(
            make_factor_df().drop(columns=["factor_value"]),
            make_forward_returns(),
            factor_names=["factor_a"],
            horizon=20,
        )


def test_fit_predict_ridge_walk_forward_outputs_predicted_return() -> None:
    predictions = fit_predict_ridge_walk_forward(
        make_model_dataset(),
        feature_cols=["feature_1", "feature_2"],
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert "predicted_return" in predictions.columns
    assert set(predictions["model_type"]) == {"ridge"}


def test_ridge_scaler_fits_each_training_split_only(
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

    monkeypatch.setattr(ridge_model, "StandardScaler", SpyScaler)

    fit_predict_ridge_walk_forward(
        data,
        feature_cols=["feature_1", "feature_2"],
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert len(SpyScaler.fit_indexes) == len(splits)
    for fit_indexes, split in zip(SpyScaler.fit_indexes, splits, strict=True):
        assert fit_indexes == split["train_index"]
        assert len(fit_indexes) < len(data)


def test_ridge_test_rows_do_not_participate_in_fit(
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

    monkeypatch.setattr(ridge_model, "StandardScaler", SpyScaler)

    fit_predict_ridge_walk_forward(
        data,
        feature_cols=["feature_1", "feature_2"],
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    for fit_indexes, split in zip(SpyScaler.fit_indexes, splits, strict=True):
        assert set(fit_indexes).isdisjoint(split["test_index"])


def test_ridge_nan_feature_rows_are_dropped_safely() -> None:
    data = make_model_dataset()
    data.loc[12, "feature_1"] = np.nan

    predictions = fit_predict_ridge_walk_forward(
        data,
        feature_cols=["feature_1", "feature_2"],
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert pd.Timestamp("2019-01-01") not in set(predictions["date"])
