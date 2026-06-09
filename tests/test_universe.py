from pathlib import Path

import pytest

from stock_alpha_lab.data_sources.universe import (
    load_market_regime,
    load_position_rules,
    load_supply_chain_map,
    load_thesis_tracker,
)

SUPPLY_CHAIN_COLUMNS = [
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
]

THESIS_TRACKER_COLUMNS = [
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
]


def write_text_file(path: Path, content: str) -> Path:
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def valid_supply_chain_csv(ticker: str = "NVDA") -> str:
    values = [
        ticker,
        "NVIDIA",
        "AI Compute",
        "GPU/Accelerator",
        "GPU",
        "AI data center capex",
        "compute platform",
        "medium",
        "high",
        "valuation/export control",
    ]
    return "\n".join([",".join(SUPPLY_CHAIN_COLUMNS), ",".join(values)])


def valid_thesis_tracker_csv(
    source_style: str = "manual",
    conviction: str = "3",
    evidence_level: str = "1",
) -> str:
    values = [
        "2026-06-09",
        "internal",
        source_style,
        "nvda",
        "supply_chain",
        "Example thesis",
        "Example why now",
        "Example catalyst",
        "Example invalidation",
        conviction,
        evidence_level,
    ]
    return "\n".join([",".join(THESIS_TRACKER_COLUMNS), ",".join(values)])


def valid_market_regime_csv() -> str:
    return """
date,spy_trend,qqq_trend,smh_trend,market_volume_state,ai_sector_state,risk_state,notes
2026-06-09,unknown,unknown,unknown,unknown,watch,neutral,Manual placeholder only.
"""


def valid_position_rules_yaml() -> str:
    return """
max_single_position_pct: 0.10
drawdown_comfort_test:
  enabled: true
entry_rules: []
avoid_rules: []
"""


def test_load_supply_chain_map_reads_valid_file(tmp_path: Path) -> None:
    csv_path = write_text_file(
        tmp_path / "supply_chain_map.csv",
        valid_supply_chain_csv(),
    )

    df = load_supply_chain_map(csv_path)

    assert list(df["ticker"]) == ["NVDA"]
    assert df.loc[0, "replaceability"] == "medium"


def test_load_supply_chain_map_missing_ticker_raises(tmp_path: Path) -> None:
    values = [
        "NVIDIA",
        "AI Compute",
        "GPU/Accelerator",
        "GPU",
        "AI data center capex",
        "compute platform",
        "medium",
        "high",
        "valuation/export control",
    ]
    csv_path = write_text_file(
        tmp_path / "supply_chain_map.csv",
        "\n".join([",".join(SUPPLY_CHAIN_COLUMNS[1:]), ",".join(values)]),
    )

    with pytest.raises(ValueError, match="ticker"):
        load_supply_chain_map(csv_path)


def test_load_supply_chain_map_uppercases_ticker(tmp_path: Path) -> None:
    csv_path = write_text_file(
        tmp_path / "supply_chain_map.csv",
        valid_supply_chain_csv(ticker="nvda"),
    )

    df = load_supply_chain_map(csv_path)

    assert df.loc[0, "ticker"] == "NVDA"


def test_load_thesis_tracker_invalid_source_style_raises(tmp_path: Path) -> None:
    csv_path = write_text_file(
        tmp_path / "thesis_tracker.csv",
        valid_thesis_tracker_csv(source_style="unsupported"),
    )

    with pytest.raises(ValueError, match="source_style"):
        load_thesis_tracker(csv_path)


def test_load_thesis_tracker_invalid_conviction_raises(tmp_path: Path) -> None:
    csv_path = write_text_file(
        tmp_path / "thesis_tracker.csv",
        valid_thesis_tracker_csv(conviction="6"),
    )

    with pytest.raises(ValueError, match="conviction"):
        load_thesis_tracker(csv_path)


def test_load_market_regime_reads_valid_file(tmp_path: Path) -> None:
    csv_path = write_text_file(
        tmp_path / "market_regime.csv",
        valid_market_regime_csv(),
    )

    df = load_market_regime(csv_path)

    assert len(df) == 1
    assert "date" in df.columns


def test_load_position_rules_reads_valid_file(tmp_path: Path) -> None:
    yaml_path = write_text_file(
        tmp_path / "position_rules.yaml",
        valid_position_rules_yaml(),
    )

    rules = load_position_rules(yaml_path)

    assert rules["max_single_position_pct"] == 0.10


def test_load_position_rules_missing_key_raises(tmp_path: Path) -> None:
    yaml_path = write_text_file(
        tmp_path / "position_rules.yaml",
        """
max_single_position_pct: 0.10
drawdown_comfort_test:
  enabled: true
entry_rules: []
""",
    )

    with pytest.raises(ValueError, match="avoid_rules"):
        load_position_rules(yaml_path)
