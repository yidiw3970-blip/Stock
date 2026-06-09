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
    PROJECT_OVERVIEW.md
  scripts/
  src/
    stock_alpha_lab/
      __init__.py
      config.py
      cli.py
      data_sources/
      factors/
      research/
      models/
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
