"""Serenity Lens inspired hypothesis feature engineering."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

SUPPLY_CHAIN_REQUIRED_COLUMNS = {
    "ticker",
    "theme",
    "layer",
    "sub_layer",
    "bottleneck_type",
    "replaceability",
    "capacity_constraint",
    "main_risk",
}

THESIS_REQUIRED_COLUMNS = {
    "date",
    "ticker",
    "thesis",
    "catalyst",
    "invalidation",
    "conviction",
    "evidence_level",
}

OUTPUT_COLUMNS = [
    "ticker",
    "theme",
    "layer",
    "sub_layer",
    "bottleneck_type",
    "replaceability_numeric",
    "capacity_constraint_numeric",
    "upstream_layer_numeric",
    "evidence_level",
    "conviction",
    "thesis_age_days",
    "thesis_count",
    "latest_thesis",
    "catalyst",
    "invalidation",
    "main_risk",
    "dilution_risk_flag",
    "serenity_hypothesis_strength",
    "serenity_missing_reason",
]

REPLACEABILITY_MAP = {"low": 100.0, "medium": 50.0, "high": 0.0}
CAPACITY_CONSTRAINT_MAP = {"high": 100.0, "medium": 50.0, "low": 0.0}
UPSTREAM_KEYWORD_MAP = {
    "hbm": 100.0,
    "inp": 95.0,
    "cpo": 92.0,
    "optical": 90.0,
    "memory": 88.0,
    "power": 85.0,
    "nuclear": 85.0,
    "grid": 80.0,
    "asic": 78.0,
    "networking": 75.0,
}
DILUTION_PATTERN = re.compile(
    r"\b(dilution|atm|offering|share issuance|equity raise)\b",
    flags=re.IGNORECASE,
)


def compute_serenity_factors(
    supply_chain_map: pd.DataFrame,
    thesis_tracker: pd.DataFrame | None = None,
    as_of_date: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Compute Serenity Lens inspired candidate hypothesis features."""

    _require_columns(
        supply_chain_map, SUPPLY_CHAIN_REQUIRED_COLUMNS, "supply_chain_map"
    )
    as_of = _resolve_as_of_date(as_of_date)
    supply = _prepare_supply_chain_map(supply_chain_map)
    thesis_by_ticker = _prepare_latest_thesis_by_ticker(thesis_tracker, as_of)

    rows = [
        _build_serenity_row(row, thesis_by_ticker.get(row["ticker"]), thesis_tracker)
        for row in supply.to_dict("records")
    ]
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def _prepare_supply_chain_map(supply_chain_map: pd.DataFrame) -> pd.DataFrame:
    df = supply_chain_map.copy()
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df = df.drop_duplicates(subset=["ticker"], keep="first")
    df["replaceability_numeric"] = _map_required_values(
        df["replaceability"],
        REPLACEABILITY_MAP,
        "replaceability",
    )
    df["capacity_constraint_numeric"] = _map_required_values(
        df["capacity_constraint"],
        CAPACITY_CONSTRAINT_MAP,
        "capacity_constraint",
    )
    upstream_values = df.apply(_map_upstream_layer, axis=1, result_type="expand")
    df["upstream_layer_numeric"] = upstream_values[0]
    df["upstream_missing_reason"] = upstream_values[1]
    return df


def _prepare_latest_thesis_by_ticker(
    thesis_tracker: pd.DataFrame | None,
    as_of_date: pd.Timestamp,
) -> dict[str, dict[str, Any]]:
    if thesis_tracker is None or thesis_tracker.empty:
        return {}

    _require_columns(thesis_tracker, THESIS_REQUIRED_COLUMNS, "thesis_tracker")
    thesis = thesis_tracker.copy()
    thesis["ticker"] = thesis["ticker"].astype("string").str.strip().str.upper()
    thesis["date"] = pd.to_datetime(thesis["date"], errors="raise")
    thesis["conviction"] = pd.to_numeric(thesis["conviction"], errors="coerce")
    thesis["evidence_level"] = pd.to_numeric(thesis["evidence_level"], errors="coerce")
    thesis = thesis[thesis["date"] <= as_of_date].sort_values(["ticker", "date"])

    latest_by_ticker: dict[str, dict[str, Any]] = {}
    for ticker, ticker_thesis in thesis.groupby("ticker", sort=False):
        latest = ticker_thesis.iloc[-1]
        latest_by_ticker[str(ticker)] = {
            "latest": latest,
            "count": int(len(ticker_thesis)),
            "age_days": int((as_of_date - latest["date"]).days),
        }

    return latest_by_ticker


def _build_serenity_row(
    supply_row: dict[str, Any],
    thesis_record: dict[str, Any] | None,
    thesis_tracker: pd.DataFrame | None,
) -> dict[str, Any]:
    missing_reasons: list[str] = []
    evidence_level = np.nan
    conviction = np.nan
    thesis_age_days = np.nan
    thesis_count = 0
    latest_thesis = pd.NA
    catalyst = pd.NA
    invalidation = pd.NA

    if thesis_record is None:
        if thesis_tracker is None or thesis_tracker.empty:
            missing_reasons.append("missing thesis_tracker")
        else:
            missing_reasons.append("missing ticker thesis")
    else:
        latest = thesis_record["latest"]
        evidence_level = latest["evidence_level"]
        conviction = latest["conviction"]
        thesis_age_days = thesis_record["age_days"]
        thesis_count = thesis_record["count"]
        latest_thesis = latest["thesis"]
        catalyst = latest["catalyst"]
        invalidation = latest["invalidation"]

    if pd.isna(evidence_level):
        missing_reasons.append("missing evidence_level")
    if pd.isna(conviction):
        missing_reasons.append("missing conviction")
    if supply_row["upstream_missing_reason"]:
        missing_reasons.append(supply_row["upstream_missing_reason"])

    dilution_risk_flag = _has_dilution_risk(
        supply_row.get("main_risk", ""),
        invalidation,
    )
    strength = _compute_hypothesis_strength(
        replaceability=supply_row["replaceability_numeric"],
        capacity_constraint=supply_row["capacity_constraint_numeric"],
        upstream_layer=supply_row["upstream_layer_numeric"],
        evidence_level=evidence_level,
        conviction=conviction,
        dilution_risk_flag=dilution_risk_flag,
    )

    return {
        "ticker": supply_row["ticker"],
        "theme": supply_row["theme"],
        "layer": supply_row["layer"],
        "sub_layer": supply_row["sub_layer"],
        "bottleneck_type": supply_row["bottleneck_type"],
        "replaceability_numeric": supply_row["replaceability_numeric"],
        "capacity_constraint_numeric": supply_row["capacity_constraint_numeric"],
        "upstream_layer_numeric": supply_row["upstream_layer_numeric"],
        "evidence_level": evidence_level,
        "conviction": conviction,
        "thesis_age_days": thesis_age_days,
        "thesis_count": thesis_count,
        "latest_thesis": latest_thesis,
        "catalyst": catalyst,
        "invalidation": invalidation,
        "main_risk": supply_row["main_risk"],
        "dilution_risk_flag": dilution_risk_flag,
        "serenity_hypothesis_strength": strength,
        "serenity_missing_reason": "; ".join(missing_reasons),
    }


def _compute_hypothesis_strength(
    replaceability: float,
    capacity_constraint: float,
    upstream_layer: float,
    evidence_level: float,
    conviction: float,
    dilution_risk_flag: bool,
) -> float:
    evidence_level_scaled = _scale_optional_level(evidence_level)
    conviction_scaled = _scale_optional_level(conviction)
    strength = (
        0.25 * replaceability
        + 0.25 * capacity_constraint
        + 0.20 * upstream_layer
        + 0.15 * evidence_level_scaled
        + 0.15 * conviction_scaled
    )

    if dilution_risk_flag:
        strength *= 0.85

    return round(float(strength), 2)


def _map_required_values(
    values: pd.Series,
    mapping: dict[str, float],
    column: str,
) -> pd.Series:
    normalized = values.astype("string").str.strip().str.lower()
    mapped = normalized.map(mapping)

    if mapped.isna().any():
        invalid_values = sorted(normalized[mapped.isna()].dropna().unique())
        invalid = ", ".join(invalid_values) if invalid_values else "<missing>"
        raise ValueError(f"Column '{column}' contains invalid values: {invalid}")

    return mapped


def _map_upstream_layer(row: pd.Series) -> tuple[float, str]:
    text = f"{row.get('layer', '')} {row.get('sub_layer', '')}".lower()

    for keyword, value in UPSTREAM_KEYWORD_MAP.items():
        if keyword in text:
            return value, ""

    return 50.0, "unknown upstream layer"


def _scale_optional_level(value: float) -> float:
    if pd.isna(value):
        return 50.0
    return float(value) / 5 * 100


def _has_dilution_risk(main_risk: object, invalidation: object) -> bool:
    text = f"{main_risk} {'' if pd.isna(invalidation) else invalidation}"
    return bool(DILUTION_PATTERN.search(text))


def _resolve_as_of_date(as_of_date: str | pd.Timestamp | None) -> pd.Timestamp:
    if as_of_date is None:
        return pd.Timestamp.today().normalize()
    return pd.Timestamp(as_of_date).normalize()


def _require_columns(
    df: pd.DataFrame, required_columns: set[str], dataset_name: str
) -> None:
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")
