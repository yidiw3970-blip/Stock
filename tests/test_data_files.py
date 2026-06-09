import csv
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WATCHLISTS_DIR = PROJECT_ROOT / "data" / "watchlists"


def read_csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as file:
        return next(csv.reader(file))


def test_watchlist_files_exist() -> None:
    expected_files = [
        "supply_chain_map.csv",
        "thesis_tracker.csv",
        "market_regime.csv",
        "position_rules.yaml",
    ]

    for filename in expected_files:
        assert (WATCHLISTS_DIR / filename).exists()


def test_supply_chain_map_has_ticker_field() -> None:
    header = read_csv_header(WATCHLISTS_DIR / "supply_chain_map.csv")

    assert "ticker" in header


def test_thesis_tracker_has_required_fields() -> None:
    header = read_csv_header(WATCHLISTS_DIR / "thesis_tracker.csv")

    assert "source_style" in header
    assert "conviction" in header
    assert "evidence_level" in header


def test_market_regime_has_date_field() -> None:
    header = read_csv_header(WATCHLISTS_DIR / "market_regime.csv")

    assert "date" in header


def test_position_rules_yaml_loads() -> None:
    with (WATCHLISTS_DIR / "position_rules.yaml").open(encoding="utf-8") as file:
        rules = yaml.safe_load(file)

    assert rules["research_only"] is True
