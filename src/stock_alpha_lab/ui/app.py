"""Minimal Streamlit app for Stock Alpha Lab."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from stock_alpha_lab.data_sources.universe import load_supply_chain_map

SUPPLY_CHAIN_MAP_PATH = Path("data/watchlists/supply_chain_map.csv")


def main() -> None:
    """Render the initial project status page."""

    st.set_page_config(page_title="Stock Alpha Lab")
    st.title("Stock Alpha Lab")
    st.subheader(
        "Quant factor research platform inspired by Serenity Lens and JACKAL Lens"
    )
    st.warning("Research only. Not financial advice.")
    st.info("Project scaffold initialized.")
    render_research_universe()


def render_research_universe() -> None:
    """Render the local research universe template."""

    st.header("Research Universe")

    try:
        supply_chain_map = load_supply_chain_map(SUPPLY_CHAIN_MAP_PATH)
    except (FileNotFoundError, OSError, ValueError) as exc:
        st.warning(f"Unable to load research universe: {exc}")
        return

    st.dataframe(supply_chain_map, use_container_width=True)


if __name__ == "__main__":
    main()
