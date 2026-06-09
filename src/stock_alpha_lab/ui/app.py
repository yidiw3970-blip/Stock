"""Minimal Streamlit app for Stock Alpha Lab."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Render the initial project status page."""

    st.set_page_config(page_title="Stock Alpha Lab")
    st.title("Stock Alpha Lab")
    st.subheader(
        "Quant factor research platform inspired by Serenity Lens and JACKAL Lens"
    )
    st.warning("Research only. Not financial advice.")
    st.info("Project scaffold initialized.")


if __name__ == "__main__":
    main()
