"""Walk-forward Ridge return prediction research helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from stock_alpha_lab.models.walk_forward import (
    make_walk_forward_splits,
    validate_no_time_leakage,
)

FACTOR_REQUIRED_COLUMNS = {"date", "ticker", "factor_name", "factor_value"}
FORWARD_RETURN_REQUIRED_COLUMNS = {
    "date",
    "ticker",
    "horizon",
    "forward_return",
}
RIDGE_OUTPUT_COLUMNS = [
    "date",
    "ticker",
    "y_true",
    "predicted_return",
    "split_id",
    "train_start",
    "train_end",
    "test_start",
    "test_end",
    "model_type",
    "alpha",
]


def prepare_regression_dataset(
    factor_df: pd.DataFrame,
    forward_return_df: pd.DataFrame,
    factor_names: list[str],
    horizon: int,
    target_col_name: str = "target_return",
) -> pd.DataFrame:
    """Prepare a wide regression dataset from long factor and return tables."""

    resolved_factor_names = _resolve_factor_names(factor_names)
    if target_col_name in resolved_factor_names:
        raise ValueError("target_col_name must not match a factor name.")

    factors = _prepare_factor_df(factor_df)
    forward_returns = _prepare_forward_return_df(forward_return_df)
    wide_factors = _pivot_factors(factors, resolved_factor_names)
    target = (
        forward_returns[forward_returns["horizon"] == int(horizon)]
        .loc[:, ["date", "ticker", "forward_return"]]
        .rename(columns={"forward_return": target_col_name})
    )
    dataset = wide_factors.merge(target, on=["date", "ticker"], how="inner")
    output_columns = ["date", "ticker", target_col_name, *resolved_factor_names]

    return (
        dataset.loc[:, output_columns]
        .sort_values(["date", "ticker"])
        .reset_index(drop=True)
    )


def fit_predict_ridge_walk_forward(
    dataset: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "target_return",
    date_col: str = "date",
    ticker_col: str = "ticker",
    train_years: int = 3,
    test_months: int = 6,
    step_months: int | None = None,
    alpha: float = 1.0,
    min_train_obs: int = 50,
) -> pd.DataFrame:
    """Fit Ridge models through chronological walk-forward splits."""

    resolved_features = _resolve_feature_cols(feature_cols)
    _require_columns(dataset, {date_col, target_col, *resolved_features}, "dataset")
    df = _prepare_model_dataset(dataset, date_col=date_col, ticker_col=ticker_col)
    splits = make_walk_forward_splits(
        data=df,
        date_col=date_col,
        train_years=train_years,
        test_months=test_months,
        step_months=step_months,
        min_train_obs=min_train_obs,
    )
    validate_no_time_leakage(splits, df, date_col=date_col)
    prediction_frames = []

    for split in splits:
        train_df = _drop_model_na(
            df.loc[split["train_index"]],
            resolved_features,
            target_col,
        )
        test_df = _drop_model_na(
            df.loc[split["test_index"]],
            resolved_features,
            target_col,
        )

        if train_df.empty or test_df.empty:
            continue

        scaler = StandardScaler()
        x_train = scaler.fit_transform(train_df.loc[:, resolved_features])
        x_test = scaler.transform(test_df.loc[:, resolved_features])
        model = Ridge(alpha=alpha)
        model.fit(x_train, train_df[target_col])
        predictions = model.predict(x_test)
        prediction_frames.append(
            _build_prediction_frame(
                test_df=test_df,
                predictions=predictions,
                split=split,
                date_col=date_col,
                ticker_col=ticker_col,
                target_col=target_col,
                alpha=alpha,
            )
        )

    if not prediction_frames:
        raise ValueError("No Ridge walk-forward predictions were produced.")

    return (
        pd.concat(prediction_frames, ignore_index=True)
        .loc[:, RIDGE_OUTPUT_COLUMNS]
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
    alpha: float,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": test_df[date_col].to_numpy(),
            "ticker": test_df[ticker_col].to_numpy()
            if ticker_col in test_df.columns
            else "",
            "y_true": test_df[target_col].to_numpy(),
            "predicted_return": predictions,
            "split_id": split["split_id"],
            "train_start": split["train_start"],
            "train_end": split["train_end"],
            "test_start": split["test_start"],
            "test_end": split["test_end"],
            "model_type": "ridge",
            "alpha": alpha,
        },
        index=test_df.index,
    )


def _prepare_factor_df(factor_df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(factor_df, FACTOR_REQUIRED_COLUMNS, "factor_df")
    df = factor_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df["factor_name"] = df["factor_name"].astype("string").str.strip()
    df["factor_value"] = pd.to_numeric(df["factor_value"], errors="coerce")
    return df


def _prepare_forward_return_df(forward_return_df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        forward_return_df,
        FORWARD_RETURN_REQUIRED_COLUMNS,
        "forward_return_df",
    )
    df = forward_return_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df["horizon"] = pd.to_numeric(df["horizon"], errors="raise").astype("int64")
    df["forward_return"] = pd.to_numeric(df["forward_return"], errors="coerce")
    return df


def _prepare_model_dataset(
    dataset: pd.DataFrame,
    date_col: str,
    ticker_col: str,
) -> pd.DataFrame:
    df = dataset.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="raise")
    if ticker_col in df.columns:
        df[ticker_col] = df[ticker_col].astype("string").str.strip().str.upper()
    return df.sort_values(date_col)


def _pivot_factors(
    factors: pd.DataFrame,
    factor_names: list[str],
) -> pd.DataFrame:
    filtered = factors[factors["factor_name"].isin(factor_names)].copy()
    if filtered.empty:
        return pd.DataFrame(columns=["date", "ticker", *factor_names])

    wide = filtered.pivot_table(
        index=["date", "ticker"],
        columns="factor_name",
        values="factor_value",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None

    for factor_name in factor_names:
        if factor_name not in wide.columns:
            wide[factor_name] = pd.NA

    return wide.loc[:, ["date", "ticker", *factor_names]]


def _drop_model_na(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
) -> pd.DataFrame:
    return df.dropna(subset=[*feature_cols, target_col])


def _resolve_factor_names(factor_names: list[str]) -> list[str]:
    resolved = [str(name).strip() for name in factor_names if str(name).strip()]
    resolved = list(dict.fromkeys(resolved))
    if not resolved:
        raise ValueError("factor_names must contain at least one factor.")
    return resolved


def _resolve_feature_cols(feature_cols: list[str]) -> list[str]:
    resolved = [str(column).strip() for column in feature_cols if str(column).strip()]
    resolved = list(dict.fromkeys(resolved))
    if not resolved:
        raise ValueError("feature_cols must contain at least one column.")
    return resolved


def _require_columns(
    df: pd.DataFrame,
    required_columns: set[str],
    dataset_name: str,
) -> None:
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")
