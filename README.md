# stock-alpha-lab

stock-alpha-lab is a local-first Python research platform for quantitative stock factor research.

The project studies alpha hypotheses inspired by public market narratives, then validates them with statistical tests. It does not provide investment advice, does not produce buy/sell recommendations, and does not automate trading.

## Current Status

Initial documentation and rule skeleton only. No production research engine or complex code has been implemented yet.

## Core Idea

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
  docs/
    PROJECT_OVERVIEW.md
```

Future code can be added only after the research rules are stable.

## Development Rules

- Keep changes small and reviewable.
- Explain changes in Chinese.
- Write code comments in English.
- Report changed files after each step.
- Never hardcode secrets.
- Never fabricate market or financial data.

