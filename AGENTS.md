# stock-alpha-lab Agent Instructions

This repository is a local-first quantitative factor research platform for stock alpha hypotheses. It is not an automated trading system and must not provide investment advice.

## Communication

- Explain work to the repository owner in Chinese unless they ask otherwise.
- Code comments, docstrings, and inline technical comments must be written in English.
- After each development step, report which files changed.
- Keep changes small and commit-ready. Prefer small commits with one clear purpose.

## Project Boundaries

- Do not implement automated trading, order routing, broker integrations, or buy/sell recommendation logic.
- Do not hardcode API keys, tokens, credentials, or private endpoints.
- Do not fabricate financial, market, fundamentals, or alternative data. If data is missing, mark it as missing.
- Do not treat public creator commentary as evidence. It can only seed alpha hypotheses and feature ideas.
- Do not produce output that tells users to buy, sell, short, hold, or size a position.

## Research Standards

- Every factor must be testable and reproducible.
- Subjective scoring is not allowed unless it is converted into observable, documented, data-driven features.
- Statistical evidence should include, where applicable:
  - Information Coefficient (IC) and rank IC.
  - Quantile or grouped forward returns.
  - Out-of-sample or walk-forward validation.
  - Robustness checks across market regimes, sectors, liquidity buckets, and time windows.
  - Clear handling of multiple testing, look-ahead bias, survivorship bias, and data revisions.
- Output should focus on research priority, statistical support, risk warnings, and observation state.

## Development Style

- Prefer simple, auditable Python modules over large frameworks until the project needs more structure.
- Keep notebooks exploratory; move reusable logic into versioned Python modules.
- Store configuration in files or environment variables, never in source code secrets.
- Make data provenance visible: source, timestamp, refresh policy, and known limitations.
- Add tests when logic becomes reusable or when a change can affect research results.

