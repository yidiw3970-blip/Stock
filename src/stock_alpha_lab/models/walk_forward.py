"""Walk-forward validation helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd

REQUIRED_SPLIT_FIELDS = {
    "split_id",
    "train_start",
    "train_end",
    "test_start",
    "test_end",
    "train_index",
    "test_index",
}


def make_walk_forward_splits(
    data: pd.DataFrame,
    date_col: str = "date",
    train_years: int = 3,
    test_months: int = 6,
    step_months: int | None = None,
    min_train_obs: int = 50,
) -> list[dict[str, Any]]:
    """Create chronological walk-forward train/test splits."""

    _validate_split_params(
        train_years=train_years,
        test_months=test_months,
        step_months=step_months,
        min_train_obs=min_train_obs,
    )
    df = _prepare_date_frame(data, date_col)

    if df.empty:
        return []

    resolved_step_months = test_months if step_months is None else step_months
    min_date = df[date_col].min()
    max_date = df[date_col].max()
    current_test_start = min_date + pd.DateOffset(years=train_years)
    splits: list[dict[str, Any]] = []

    while current_test_start <= max_date:
        train_start_boundary = current_test_start - pd.DateOffset(years=train_years)
        test_end_exclusive = current_test_start + pd.DateOffset(months=test_months)
        train_mask = (df[date_col] >= train_start_boundary) & (
            df[date_col] < current_test_start
        )
        test_mask = (df[date_col] >= current_test_start) & (
            df[date_col] < test_end_exclusive
        )
        train_df = df.loc[train_mask]
        test_df = df.loc[test_mask]

        if len(train_df) >= min_train_obs and not test_df.empty:
            splits.append(
                {
                    "split_id": len(splits),
                    "train_start": train_df[date_col].min(),
                    "train_end": train_df[date_col].max(),
                    "test_start": test_df[date_col].min(),
                    "test_end": test_df[date_col].max(),
                    "train_index": train_df.index.to_list(),
                    "test_index": test_df.index.to_list(),
                }
            )

        current_test_start = current_test_start + pd.DateOffset(
            months=resolved_step_months
        )

    return splits


def validate_no_time_leakage(
    splits: list[dict[str, Any]],
    data: pd.DataFrame,
    date_col: str = "date",
) -> None:
    """Validate that every split trains strictly before it tests."""

    if not splits:
        raise ValueError("splits must not be empty.")

    df = _prepare_date_frame(data, date_col)

    for split in splits:
        _require_split_fields(split)
        try:
            train_dates = df.loc[split["train_index"], date_col]
            test_dates = df.loc[split["test_index"], date_col]
        except KeyError as exc:
            raise ValueError("split indexes must exist in data.") from exc

        if train_dates.empty or test_dates.empty:
            raise ValueError("split train_index and test_index must not be empty.")

        if train_dates.max() >= test_dates.min():
            raise ValueError(f"Time leakage detected in split {split['split_id']}.")


def fit_predict_walk_forward(
    model: Any,
    data: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    date_col: str = "date",
    ticker_col: str = "ticker",
    train_years: int = 3,
    test_months: int = 6,
    step_months: int | None = None,
    min_train_obs: int = 50,
    prediction_col: str = "prediction",
) -> pd.DataFrame:
    """Fit a model on each training window and predict each test window."""

    _require_columns(data, [date_col, target_col, *feature_cols], "data")
    splits = make_walk_forward_splits(
        data=data,
        date_col=date_col,
        train_years=train_years,
        test_months=test_months,
        step_months=step_months,
        min_train_obs=min_train_obs,
    )
    validate_no_time_leakage(splits, data, date_col=date_col)
    df = _prepare_date_frame(data, date_col)
    prediction_frames = []

    for split in splits:
        train_df = _drop_model_na(
            df.loc[split["train_index"]],
            feature_cols,
            target_col,
        )
        test_df = _drop_model_na(df.loc[split["test_index"]], feature_cols, target_col)

        if train_df.empty or test_df.empty:
            continue

        model.fit(train_df.loc[:, feature_cols], train_df[target_col])
        predictions = model.predict(test_df.loc[:, feature_cols])
        prediction_frames.append(
            _build_prediction_frame(
                test_df=test_df,
                predictions=predictions,
                split=split,
                date_col=date_col,
                ticker_col=ticker_col,
                target_col=target_col,
                prediction_col=prediction_col,
            )
        )

    if not prediction_frames:
        raise ValueError("No walk-forward predictions were produced.")

    return (
        pd.concat(prediction_frames, ignore_index=True)
        .sort_values(["date", "split_id", "ticker"])
        .reset_index(drop=True)
    )


def _build_prediction_frame(
    test_df: pd.DataFrame,
    predictions: Any,
    split: dict[str, Any],
    date_col: str,
    ticker_col: str,
    target_col: str,
    prediction_col: str,
) -> pd.DataFrame:
    output = pd.DataFrame(
        {
            "date": test_df[date_col].to_numpy(),
            "ticker": test_df[ticker_col].to_numpy()
            if ticker_col in test_df.columns
            else "",
            "y_true": test_df[target_col].to_numpy(),
            prediction_col: predictions,
            "split_id": split["split_id"],
            "train_start": split["train_start"],
            "train_end": split["train_end"],
            "test_start": split["test_start"],
            "test_end": split["test_end"],
        },
        index=test_df.index,
    )
    return output


def _drop_model_na(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
) -> pd.DataFrame:
    return df.dropna(subset=[*feature_cols, target_col])


def _prepare_date_frame(data: pd.DataFrame, date_col: str) -> pd.DataFrame:
    _require_columns(data, [date_col], "data")
    df = data.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="raise")
    return df.sort_values(date_col)


def _validate_split_params(
    train_years: int,
    test_months: int,
    step_months: int | None,
    min_train_obs: int,
) -> None:
    if train_years <= 0:
        raise ValueError("train_years must be positive.")
    if test_months <= 0:
        raise ValueError("test_months must be positive.")
    if step_months is not None and step_months <= 0:
        raise ValueError("step_months must be positive when provided.")
    if min_train_obs <= 0:
        raise ValueError("min_train_obs must be positive.")


def _require_split_fields(split: dict[str, Any]) -> None:
    missing_fields = REQUIRED_SPLIT_FIELDS.difference(split)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"split is missing required fields: {missing}")


def _require_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str,
) -> None:
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")
