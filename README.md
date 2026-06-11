# stock-alpha-lab

stock-alpha-lab is a local-first Python research platform for quantitative stock factor research.

The project studies alpha hypotheses inspired by public market narratives, then validates them with statistical tests. It does not provide investment advice, does not produce buy/sell recommendations, and does not automate trading.

Research only. Not financial advice. No auto-trading.

## Current Status

Project scaffold initialized. No production research engine, data download workflow, stock-selection logic, or trading logic has been implemented.

## Project Positioning

The project references two public X creator styles as hypothesis sources:

- Serenity Lens: AI and semiconductor supply-chain bottlenecks, upstream constraints, CPO, HBM, InP, Neocloud, power infrastructure, robotics, and related themes.
- JACKAL Lens: market tempo, relative strength, SPY/QQQ/SMH state, pullback quality, volatility, breadth, and position-comfort context.

These ideas are not scores and not evidence. They only guide feature engineering. Every factor must be validated statistically before it can be treated as research-supported.

## Non-Goals

- No automated trading.
- No broker integration.
- No order placement.
- No buy/sell/hold advice.
- No hardcoded API keys or credentials.
- No fabricated financial data.

## Installation

Use Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Copy the example environment file before adding local values:

```powershell
Copy-Item .env.example .env
```

Never commit `.env` or any secrets.

## Test

```powershell
pytest
```

## Lint

```powershell
ruff check .
```

## Run Streamlit

```powershell
streamlit run src/stock_alpha_lab/ui/app.py
```

The initial app only shows project status and research-only warnings.

## Price Data Prototype

The project includes a yfinance-based downloader for research prototypes only. The project does not claim yfinance is an official Yahoo data source, and downloaded prices must not be treated as production-grade or guaranteed for live trading.

Run the default price update:

```powershell
python scripts/update_prices.py --start 2020-01-01
```

The script reads tickers from `data/watchlists/supply_chain_map.csv` and writes normalized OHLCV data to:

```text
data/raw/prices.csv
```

Supported options:

```powershell
python scripts/update_prices.py --start 2020-01-01 --end 2026-01-01 --output data/raw/prices.csv
```

Downloaded data is for research only. Not financial advice. No auto-trading.

Data quality limitations:

- yfinance is suitable here only as a convenient research prototype connector.
- Data may be delayed, revised, incomplete, adjusted differently than expected, or unavailable for some tickers.
- A failed ticker download is logged and skipped so other tickers can continue.
- Any serious research result should document the data source, timestamp, adjustment policy, and known gaps.

## Price Factors

The first factor module computes trailing price and liquidity features from normalized OHLCV data. It does not download data, run a backtest, create a composite score, or produce recommendations.

Definitions are documented in [docs/FACTOR_DEFINITIONS.md](docs/FACTOR_DEFINITIONS.md).

## Research Validation

Forward returns are supported as research labels for later factor validation. They are not same-day features and must not be used as trading instructions.

Walk-forward validation is supported as a chronological train/test framework. It does not implement a specific prediction model, run a backtest, or produce recommendations.

Research workflow notes are documented in [docs/QUANT_RESEARCH_FRAMEWORK.md](docs/QUANT_RESEARCH_FRAMEWORK.md) and [docs/FACTOR_VALIDATION_RULES.md](docs/FACTOR_VALIDATION_RULES.md).

## GitHub Update Flow

Repository: <https://github.com/yidiw3970-blip/Stock.git>

Use small commits:

```powershell
git status
git add <changed-files>
git commit -m "type: short description"
git pull --rebase origin main
git push origin main
```

## Research Principles

- Start with a written hypothesis.
- Build observable, reproducible features.
- Validate using IC, rank IC, grouped forward returns, and walk-forward tests.
- Track data source, timestamp, missing-data behavior, and known limitations.
- Report uncertainty, weak evidence, and failure cases plainly.

## Intended Outputs

The system should eventually output:

- Research priority.
- Statistical support.
- Confidence and robustness notes.
- Data-quality and methodology warnings.
- Observation state.

It should not output trade instructions or personalized investment recommendations.

## Planned Structure

```text
stock-alpha-lab/
  AGENTS.md
  README.md
  .cursor/
    rules/
      project-rules.mdc
      quant-rules.mdc
      ui-rules.mdc
  data/
    raw/
    processed/
    watchlists/
  docs/
    DATA_SOURCES.md
    FACTOR_DEFINITIONS.md
    FACTOR_VALIDATION_RULES.md
    PROJECT_OVERVIEW.md
    QUANT_RESEARCH_FRAMEWORK.md
  scripts/
    update_prices.py
  src/
    stock_alpha_lab/
      __init__.py
      config.py
      cli.py
      data_sources/
        yfinance_client.py
      factors/
        price_factors.py
      research/
        forward_returns.py
      models/
        walk_forward.py
      backtest/
      reports/
      ui/
        app.py
  tests/
    test_smoke.py
```

Future research code should be added only after the related hypothesis, data policy, and validation design are clear.

## Development Rules

- Keep changes small and reviewable.
- Explain changes in Chinese.
- Write code comments in English.
- Report changed files after each step.
- Never hardcode secrets.
- Never fabricate market or financial data.
