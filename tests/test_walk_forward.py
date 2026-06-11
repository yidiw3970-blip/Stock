import numpy as np
import pandas as pd
import pytest

from stock_alpha_lab.models.walk_forward import (
    fit_predict_walk_forward,
    make_walk_forward_splits,
    validate_no_time_leakage,
)


class DummyModel:
    def __init__(self) -> None:
        self.fit_indexes: list[list[int]] = []
        self.fit_target_means: list[float] = []

    def fit(self, x: pd.DataFrame, y: pd.Series) -> "DummyModel":
        self.fit_indexes.append(list(x.index))
        self.fit_target_means.append(float(y.mean()))
        return self

    def predict(self, x: pd.DataFrame) -> np.ndarray:
        return np.full(len(x), self.fit_target_means[-1])


def make_walk_data(periods: int = 48) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2018-01-01", periods=periods, freq="MS"),
            "ticker": ["AAA"] * periods,
            "feature_1": np.arange(periods, dtype=float),
            "target": np.arange(periods, dtype=float) / 100,
        }
    )


def test_make_walk_forward_splits_train_end_before_test_start() -> None:
    data = make_walk_data()

    splits = make_walk_forward_splits(
        data,
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert splits
    for split in splits:
        assert split["train_end"] < split["test_start"]


def test_make_walk_forward_splits_keeps_chronological_order() -> None:
    data = make_walk_data().sample(frac=1, random_state=1)

    splits = make_walk_forward_splits(
        data,
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )
    first_split = splits[0]
    train_dates = data.loc[first_split["train_index"], "date"]
    test_dates = data.loc[first_split["test_index"], "date"]

    assert train_dates.is_monotonic_increasing
    assert test_dates.is_monotonic_increasing
    assert train_dates.max() < test_dates.min()


def test_min_train_obs_skips_split() -> None:
    data = make_walk_data(periods=24)

    splits = make_walk_forward_splits(
        data,
        train_years=1,
        test_months=3,
        min_train_obs=100,
    )

    assert splits == []


def test_validate_no_time_leakage_raises_on_leakage() -> None:
    data = make_walk_data(periods=24)
    leaking_split = {
        "split_id": 0,
        "train_start": data.loc[0, "date"],
        "train_end": data.loc[13, "date"],
        "test_start": data.loc[12, "date"],
        "test_end": data.loc[15, "date"],
        "train_index": list(range(14)),
        "test_index": list(range(12, 16)),
    }

    with pytest.raises(ValueError, match="Time leakage"):
        validate_no_time_leakage([leaking_split], data)


def test_fit_predict_walk_forward_does_not_fit_on_test_rows() -> None:
    data = make_walk_data(periods=36)
    model = DummyModel()
    splits = make_walk_forward_splits(
        data,
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    predictions = fit_predict_walk_forward(
        model,
        data,
        feature_cols=["feature_1"],
        target_col="target",
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert not predictions.empty
    for fit_indexes, split in zip(model.fit_indexes, splits, strict=True):
        assert set(fit_indexes).isdisjoint(split["test_index"])


def test_fit_predict_walk_forward_output_columns() -> None:
    data = make_walk_data(periods=36)
    predictions = fit_predict_walk_forward(
        DummyModel(),
        data,
        feature_cols=["feature_1"],
        target_col="target",
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert {"date", "ticker", "y_true", "prediction", "split_id"}.issubset(
        predictions.columns
    )


def test_default_step_avoids_overlapping_test_windows() -> None:
    data = make_walk_data(periods=36)
    predictions = fit_predict_walk_forward(
        DummyModel(),
        data,
        feature_cols=["feature_1"],
        target_col="target",
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert not predictions.duplicated(subset=["date", "ticker"]).any()


def test_missing_feature_or_target_raises_value_error() -> None:
    data = make_walk_data(periods=24)

    with pytest.raises(ValueError, match="missing_feature"):
        fit_predict_walk_forward(
            DummyModel(),
            data,
            feature_cols=["missing_feature"],
            target_col="target",
        )

    with pytest.raises(ValueError, match="missing_target"):
        fit_predict_walk_forward(
            DummyModel(),
            data,
            feature_cols=["feature_1"],
            target_col="missing_target",
        )


def test_nan_feature_rows_are_dropped_safely() -> None:
    data = make_walk_data(periods=36)
    data.loc[12, "feature_1"] = np.nan

    predictions = fit_predict_walk_forward(
        DummyModel(),
        data,
        feature_cols=["feature_1"],
        target_col="target",
        train_years=1,
        test_months=3,
        min_train_obs=12,
    )

    assert pd.Timestamp("2019-01-01") not in set(predictions["date"])


def test_empty_splits_raise_clear_error() -> None:
    data = make_walk_data(periods=12)

    with pytest.raises(ValueError, match="splits must not be empty"):
        fit_predict_walk_forward(
            DummyModel(),
            data,
            feature_cols=["feature_1"],
            target_col="target",
            train_years=3,
            test_months=3,
            min_train_obs=12,
        )
