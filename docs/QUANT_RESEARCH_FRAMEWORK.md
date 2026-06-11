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
