"""Load and validate local research universe templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

LEVEL_VALUES = {"low", "medium", "high"}
SOURCE_STYLE_VALUES = {"serenity", "jackal", "manual"}

SUPPLY_CHAIN_REQUIRED_COLUMNS = {
    "ticker",
    "company",
    "theme",
    "layer",
    "sub_layer",
    "downstream_link",
    "bottleneck_type",
    "replaceability",
    "capacity_constraint",
    "main_risk",
}

THESIS_TRACKER_REQUIRED_COLUMNS = {
    "date",
    "source_handle",
    "source_style",
    "ticker",
    "thesis_type",
    "thesis",
    "why_now",
    "catalyst",
    "invalidation",
    "conviction",
    "evidence_level",
}

MARKET_REGIME_REQUIRED_COLUMNS = {
    "date",
    "spy_trend",
    "qqq_trend",
    "smh_trend",
    "market_volume_state",
    "ai_sector_state",
    "risk_state",
    "notes",
}

POSITION_RULES_REQUIRED_KEYS = {
    "max_single_position_pct",
    "drawdown_comfort_test",
    "entry_rules",
    "avoid_rules",
}


def load_supply_chain_map(path: str | Path) -> pd.DataFrame:
    """Load and validate the supply-chain research map."""

    df = pd.read_csv(Path(path))
    _require_columns(df, SUPPLY_CHAIN_REQUIRED_COLUMNS, "supply_chain_map.csv")
    df = df.copy()
    df["ticker"] = _normalize_ticker_column(df, "supply_chain_map.csv")
    df["replaceability"] = _normalize_allowed_values(
        df, "replaceability", LEVEL_VALUES, "supply_chain_map.csv"
    )
    df["capacity_constraint"] = _normalize_allowed_values(
        df, "capacity_constraint", LEVEL_VALUES, "supply_chain_map.csv"
    )
    df = df.drop_duplicates(subset=["ticker"], keep="first")
    return df.reset_index(drop=True)


def load_thesis_tracker(path: str | Path) -> pd.DataFrame:
    """Load and validate the thesis tracker template."""

    df = pd.read_csv(Path(path))
    _require_columns(df, THESIS_TRACKER_REQUIRED_COLUMNS, "thesis_tracker.csv")
    df = df.copy()
    df["ticker"] = _clean_text_series(df["ticker"]).str.upper()
    df["source_style"] = _normalize_allowed_values(
        df, "source_style", SOURCE_STYLE_VALUES, "thesis_tracker.csv"
    )
    df["conviction"] = _validate_integer_range(
        df, "conviction", 1, 5, "thesis_tracker.csv"
    )
    df["evidence_level"] = _validate_integer_range(
        df, "evidence_level", 1, 5, "thesis_tracker.csv"
    )
    df["date"] = _parse_date_column(df, "date", "thesis_tracker.csv")
    return df


def load_market_regime(path: str | Path) -> pd.DataFrame:
    """Load and validate the market regime template."""

    df = pd.read_csv(Path(path))
    _require_columns(df, MARKET_REGIME_REQUIRED_COLUMNS, "market_regime.csv")
    df = df.copy()
    df["date"] = _parse_date_column(df, "date", "market_regime.csv")
    return df


def load_position_rules(path: str | Path) -> dict[str, Any]:
    """Load and validate research-only position rules."""

    with Path(path).open(encoding="utf-8") as file:
        rules = yaml.safe_load(file)

    if not isinstance(rules, dict):
        raise ValueError("position_rules.yaml must contain a YAML mapping.")

    missing_keys = POSITION_RULES_REQUIRED_KEYS.difference(rules)
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"position_rules.yaml is missing required keys: {missing}")

    return rules


def _require_columns(
    df: pd.DataFrame, required_columns: set[str], dataset_name: str
) -> None:
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")


def _clean_text_series(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def _normalize_ticker_column(df: pd.DataFrame, dataset_name: str) -> pd.Series:
    tickers = _clean_text_series(df["ticker"])
    missing_tickers = tickers.isna() | tickers.eq("")

    if missing_tickers.any():
        raise ValueError(f"{dataset_name} contains empty ticker values.")

    return tickers.str.upper()


def _normalize_allowed_values(
    df: pd.DataFrame, column: str, allowed_values: set[str], dataset_name: str
) -> pd.Series:
    values = _clean_text_series(df[column]).str.lower()
    invalid_values = sorted(
        value
        for value in values.dropna().unique()
        if value not in allowed_values
    )

    if values.isna().any() or invalid_values:
        allowed = ", ".join(sorted(allowed_values))
        invalid = ", ".join(invalid_values) if invalid_values else "<missing>"
        raise ValueError(
            f"{dataset_name} column '{column}' contains invalid values: "
            f"{invalid}. Allowed values: {allowed}"
        )

    return values


def _validate_integer_range(
    df: pd.DataFrame, column: str, minimum: int, maximum: int, dataset_name: str
) -> pd.Series:
    values = pd.to_numeric(df[column], errors="coerce")
    invalid_mask = values.isna() | values.mod(1).ne(0) | values.lt(minimum) | values.gt(
        maximum
    )

    if invalid_mask.any():
        raise ValueError(
            f"{dataset_name} column '{column}' must contain integers from "
            f"{minimum} to {maximum}."
        )

    return values.astype("int64")


def _parse_date_column(
    df: pd.DataFrame, column: str, dataset_name: str
) -> pd.Series:
    try:
        return pd.to_datetime(df[column], errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{dataset_name} column '{column}' must contain parseable dates."
        ) from exc
