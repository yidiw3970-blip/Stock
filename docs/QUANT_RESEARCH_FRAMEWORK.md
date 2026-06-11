# Quant Research Framework

Research only. Not financial advice. No auto-trading.

This document describes the research role of forward returns in stock-alpha-lab.

## Forward Returns Are Labels

Forward returns are future realized returns used as research labels or targets. They are not features available on the signal date.

For a horizon `N`, the forward return is:

```text
adj_close.shift(-N) / adj_close - 1
```

This means the value is only known after `N` future observations have occurred.

## Why Forward Returns Are Needed

Factor research needs a future outcome to test whether a feature has predictive information. A candidate factor cannot be considered statistically supported until it is compared against future outcomes using methods such as:

- IC and rank IC.
- Grouped or quantile forward returns.
- Walk-forward or out-of-sample validation.
- Robustness checks across regimes, sectors, size buckets, and liquidity buckets.

The forward-return label provides the outcome side of this test.

## Avoiding Look-Ahead Bias

To avoid look-ahead bias:

- Factor values must be computed only from data available on or before `date`.
- Forward returns must never be merged into the feature set as same-day inputs.
- Any feature using revisions, restatements, or delayed publications must be timestamp-aware.
- Validation joins should align factor rows at `date` with forward-return labels that begin after `date`.
- Rows with insufficient future data should remain missing rather than being forward-filled.

## Where Forward Returns May Be Used

Allowed uses:

- Factor validation.
- IC analysis.
- Grouped forward-return analysis.
- Walk-forward research.
- Diagnostic reports about statistical support.

Disallowed uses:

- Live features.
- Trade instructions.
- Buy, sell, hold, short, target-price, or position-size outputs.
- Automated execution logic.

Forward returns are a research validation target only.

## IC Analysis

IC analysis compares factor values available at `date` with forward returns that occur after `date`. The first implementation uses Spearman rank correlation for each date, factor, and horizon.

IC is a research statistic. It can indicate whether a factor has cross-sectional ranking information in a sample, but it does not prove that the relationship will persist. It should be paired with grouped return analysis, walk-forward testing, and risk checks.

## Quantile Analysis

Quantile analysis sorts each date's cross-section into factor buckets and then compares each bucket's future returns. It helps answer whether high factor values and low factor values behaved differently in the historical sample.

The first implementation reports quantile mean returns, median returns, hit rates, counts, top-minus-bottom spreads, spread t-stats, and non-decreasing monotonic share.

These results are validation diagnostics only. They do not include trading costs, liquidity, turnover, or out-of-sample checks, and they must not be interpreted as investment advice.

## Walk-Forward Validation

Walk-forward validation tests a research workflow in chronological order. Each split uses an earlier training window and a later testing window.

Financial time series should not be randomly split because random shuffling can leak future regimes, future cross-sectional information, and post-event data into training. The validation order must respect what would have been known at the time.

Window terms:

- `train_years`: length of the rolling historical training window.
- `test_months`: length of the forward test window.
- `step_months`: how far the test window advances after each split. When `step_months` equals `test_months`, test windows do not overlap.
- `min_train_obs`: minimum training rows required to keep a split.

Look-ahead controls:

- Training dates must be strictly earlier than testing dates.
- Test data must never participate in model fitting.
- Model tuning should happen inside training windows only.
- Test windows are for evaluation, not repeated manual adjustment.

Walk-forward validation still cannot solve every problem. It does not remove survivorship bias, stale or revised data, poor vendor quality, overfitting, transaction costs, liquidity constraints, or capacity issues. It is one required validation layer, not proof of future performance.

Research only. Not financial advice.
