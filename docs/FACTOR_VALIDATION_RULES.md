# Factor Validation Rules

Research only. Not financial advice. No auto-trading.

No factor should be promoted because it sounds plausible. Serenity Lens and JACKAL Lens inspired features are alpha hypotheses only. Statistical validation decides whether a feature has research support.

## Validation Flow

The intended validation flow is:

```text
factor values -> forward returns -> IC -> quantile analysis -> walk-forward
```

Each step answers a different question:

- Factor values: what did the feature say at the observation date?
- Forward returns: what happened after the observation date?
- IC: did the feature rank future returns better than noise?
- Quantile analysis: did grouped factor buckets show monotonic or economically meaningful behavior?
- Walk-forward: did the relationship survive out-of-sample testing?

## Required Boundaries

- Factor values must be timestamp-safe and based only on data available on or before `date`.
- Forward returns must be treated as future labels, not as same-day features.
- Missing labels should remain missing.
- A single good backtest or attractive chart is not enough evidence.
- Validation must report sample size, missing-data rates, time coverage, and fragility.

## Lens Features

Serenity Lens features can help structure supply-chain bottleneck hypotheses. JACKAL Lens features can help structure market-tempo hypotheses. Neither source is evidence by itself.

Before either family of features can be treated as statistically supported, the project must test:

- IC and rank IC.
- Grouped forward returns.
- Walk-forward or out-of-sample stability.
- Robustness across market regimes, sectors, market-cap buckets, and liquidity buckets.
- Sensitivity to missing data, stale labels, and multiple testing.

## Output Policy

Allowed outputs:

- Research priority.
- Statistical support level.
- Data-quality warnings.
- Risk warnings.
- Observation state.

Disallowed outputs:

- Buy, sell, hold, short, target price, stop loss, or position size.
- Automated trading instructions.
- Claims that a factor is valid before statistical validation.
