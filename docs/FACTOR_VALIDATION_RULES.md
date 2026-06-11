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

## Information Coefficient

Information Coefficient, or IC, measures the cross-sectional relationship between factor values and future returns on the same observation date and horizon.

The first implementation uses Spearman rank correlation because factor research usually cares about whether a feature ranks stocks in a useful order, not whether the raw feature and future returns have a linear relationship.

The connection is:

```text
factor values at date -> forward returns after date -> daily Spearman IC
```

For each `date`, `factor_name`, and `horizon`, the project aligns factor values with forward returns by `date` and `ticker`, drops missing values, and computes the rank correlation. If the cross-section is too small or either side is constant, IC remains missing.

Interpretation boundaries:

- Positive IC is statistical support, not a guaranteed future return.
- Negative IC can indicate inverse relationship, instability, or data issues.
- IC must be interpreted with sample size, coverage, and regime context.
- IC cannot be used alone as the final decision rule.

The first summary uses a plain t-stat:

```text
mean_ic / (ic_std / sqrt(ic_count))
```

This is a simple first-pass diagnostic. A later version should add Newey-West or HAC t-statistics to address time-series autocorrelation in daily IC observations.

IC should be evaluated alongside quantile analysis, walk-forward validation, transaction-cost sensitivity, liquidity constraints, and risk checks before any factor is considered statistically supported.

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
