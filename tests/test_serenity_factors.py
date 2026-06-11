import numpy as np
import pandas as pd
import pytest

from stock_alpha_lab.factors.serenity_factors import compute_serenity_factors


def supply_chain_map(
    ticker: str = "nvda",
    main_risk: str = "valuation",
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": [ticker],
            "theme": ["AI Compute"],
            "layer": ["HBM"],
            "sub_layer": ["Memory"],
            "bottleneck_type": ["memory bottleneck"],
            "replaceability": ["low"],
            "capacity_constraint": ["high"],
            "main_risk": [main_risk],
        }
    )


def thesis_tracker(
    ticker: str = "NVDA",
    evidence_level: int = 3,
    conviction: int = 3,
    invalidation: str = "validation fails",
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2026-06-01"],
            "ticker": [ticker],
            "thesis": ["HBM bottleneck hypothesis"],
            "catalyst": ["capacity update"],
            "invalidation": [invalidation],
            "conviction": [conviction],
            "evidence_level": [evidence_level],
        }
    )


def test_replaceability_low_maps_to_100() -> None:
    factors = compute_serenity_factors(
        supply_chain_map(),
        thesis_tracker(),
        as_of_date="2026-06-11",
    )

    assert factors.loc[0, "replaceability_numeric"] == 100


def test_capacity_constraint_high_maps_to_100() -> None:
    factors = compute_serenity_factors(
        supply_chain_map(),
        thesis_tracker(),
        as_of_date="2026-06-11",
    )

    assert factors.loc[0, "capacity_constraint_numeric"] == 100


def test_ticker_is_uppercased() -> None:
    factors = compute_serenity_factors(
        supply_chain_map(ticker="nvda"),
        thesis_tracker(ticker="nvda"),
        as_of_date="2026-06-11",
    )

    assert factors.loc[0, "ticker"] == "NVDA"


def test_missing_thesis_tracker_outputs_missing_reason() -> None:
    factors = compute_serenity_factors(
        supply_chain_map(),
        thesis_tracker=None,
        as_of_date="2026-06-11",
    )

    assert np.isnan(factors.loc[0, "evidence_level"])
    assert "missing thesis_tracker" in factors.loc[0, "serenity_missing_reason"]


def test_evidence_level_and_conviction_affect_hypothesis_strength() -> None:
    low_evidence = compute_serenity_factors(
        supply_chain_map(),
        thesis_tracker(evidence_level=1, conviction=1),
        as_of_date="2026-06-11",
    )
    high_evidence = compute_serenity_factors(
        supply_chain_map(),
        thesis_tracker(evidence_level=5, conviction=5),
        as_of_date="2026-06-11",
    )

    assert (
        high_evidence.loc[0, "serenity_hypothesis_strength"]
        > low_evidence.loc[0, "serenity_hypothesis_strength"]
    )


def test_dilution_risk_discounts_hypothesis_strength() -> None:
    clean = compute_serenity_factors(
        supply_chain_map(),
        thesis_tracker(),
        as_of_date="2026-06-11",
    )
    dilution = compute_serenity_factors(
        supply_chain_map(main_risk="valuation and ATM risk"),
        thesis_tracker(invalidation="share issuance would weaken hypothesis"),
        as_of_date="2026-06-11",
    )

    assert bool(dilution.loc[0, "dilution_risk_flag"]) is True
    assert (
        dilution.loc[0, "serenity_hypothesis_strength"]
        < clean.loc[0, "serenity_hypothesis_strength"]
    )


def test_missing_required_supply_column_raises_value_error() -> None:
    supply = supply_chain_map().drop(columns=["theme"])

    with pytest.raises(ValueError, match="theme"):
        compute_serenity_factors(supply, thesis_tracker())
