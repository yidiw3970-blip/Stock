# JACKAL Lens

Research only. Not financial advice. No auto-trading.

JACKAL Lens style research focuses on market tempo, relative strength, trend state, pullback quality, volatility, and comfort-zone context. In this project, that perspective is used only as an alpha hypothesis source for feature engineering.

## Research Focus

Candidate observations include:

- Relative strength versus SPY, QQQ, and SMH.
- Trend state using 50-day and 200-day moving average context.
- Pullback depth using short-term momentum.
- Realized volatility as a risk-state proxy.
- Benchmark-aware market regime context.

These observations are candidate features, not evidence that a timing rule works.

## Structured Candidate Features

`compute_jackal_factors` converts price factors into transparent market-tempo features:

- `relative_strength_vs_spy_20d`: ticker 20-day momentum minus SPY 20-day momentum on the same date.
- `relative_strength_vs_qqq_20d`: ticker 20-day momentum minus QQQ 20-day momentum on the same date.
- `relative_strength_vs_smh_20d`: ticker 20-day momentum minus SMH 20-day momentum on the same date.
- `trend_filter_50_200`: 100 when price is above both moving averages, 50 when above one, 0 when above neither.
- `pullback_depth_20d`: negative 20-day momentum as a candidate pullback-depth observation.
- `distance_to_ma50`: price distance from the 50-day moving average.
- `distance_to_ma200`: price distance from the 200-day moving average.
- `volatility_risk_bucket`: low, medium, high, or unknown based on 60-day realized volatility.
- `jackal_missing_reason`: records missing benchmark, trend, momentum, or volatility inputs.

## Timing Hypothesis Strength

`jackal_timing_hypothesis_strength` is a transparent hypothesis-strength feature, not a timing signal.

Formula:

```text
0.35 * relative_strength_component
+ 0.35 * trend_filter_50_200
+ 0.15 * pullback_component
+ 0.15 * volatility_component
```

Relative strength is clipped and mapped from `-0.10` to `+0.10` into `0` to `100`. Pullback logic gives the highest observation value to moderate pullbacks or mild strength between `-0.15` and `+0.05`, while penalizing deeper damage or excessive short-term extension. Volatility maps low, medium, high, and unknown to fixed transparent components.

## Required Validation

This module does not prove timing effectiveness. Later research must test:

- IC and rank IC.
- Grouped forward returns.
- Walk-forward or out-of-sample results.
- Performance across market regimes.
- Sensitivity to benchmark choice.
- Robustness to transaction costs and data-quality issues in any future simulation.

## Risks

- Market state can change abruptly.
- Trend features can fail during reversals.
- Pullback rules can overfit recent regimes.
- Relative strength can be crowded or unstable.
- Data source quality and corporate-action handling can distort signals.
- Missing benchmark data can produce neutral placeholders rather than evidence.

These features must not be displayed or interpreted as buy, sell, hold, short, target-price, or position-size instructions.
