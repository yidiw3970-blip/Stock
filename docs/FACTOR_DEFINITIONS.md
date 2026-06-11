# Factor Definitions

Research only. Not financial advice. No auto-trading.

This document defines the first price-based research factors in stock-alpha-lab. These factors are descriptive features derived from historical OHLCV data. They are not buy, sell, hold, target-price, or position-size signals.

## Input Assumptions

`compute_price_factors(prices)` expects a pandas DataFrame with at least:

- `date`
- `ticker`
- `adj_close`
- `volume`

The function uses `adj_close` as the primary price field, uppercases tickers, sorts by date within ticker, and computes factors using only trailing data. It does not read files, write files, download data, forward-fill missing factor values, run a backtest, or create a composite score.

## Factor List

### `momentum_20d`

Definition: `adj_close / adj_close.shift(20) - 1`

Intuition: short-term trailing price strength over roughly one trading month.

JACKAL Lens connection: useful for relative strength and short-term market-tempo observation after statistical validation.

### `momentum_60d`

Definition: `adj_close / adj_close.shift(60) - 1`

Intuition: intermediate trailing price strength over roughly one quarter.

JACKAL Lens connection: useful for trend persistence and leadership observation.

### `momentum_120d`

Definition: `adj_close / adj_close.shift(120) - 1`

Intuition: medium-term trailing price strength over roughly six months.

JACKAL Lens connection: useful for regime-aware relative strength research.

### `momentum_252d`

Definition: `adj_close / adj_close.shift(252) - 1`

Intuition: long-term trailing price strength over roughly one trading year.

JACKAL Lens connection: useful for longer-cycle leadership and trend-state observation.

### `volatility_60d`

Definition: rolling 60-day standard deviation of daily returns, annualized by `sqrt(252)`.

Intuition: recent realized price variability.

JACKAL Lens connection: useful for pullback quality, risk-state, and comfort-zone research.

### `max_drawdown_252d`

Definition: worst drawdown inside the trailing 252-day window, computed from each window's running high.

Intuition: largest peak-to-trough decline observed over roughly one trading year.

JACKAL Lens connection: useful for drawdown quality and trend damage observation.

### `rolling_high_252d`

Definition: trailing 252-day maximum of `adj_close`.

Intuition: the highest adjusted close observed over roughly one trading year.

JACKAL Lens connection: useful for trend-state and distance-from-high research.

### `rolling_low_252d`

Definition: trailing 252-day minimum of `adj_close`.

Intuition: the lowest adjusted close observed over roughly one trading year.

JACKAL Lens connection: useful for recovery quality and distance-from-low research.

### `distance_to_52w_high`

Definition: `adj_close / rolling_high_252d - 1`

Intuition: current adjusted close relative to the trailing one-year high.

JACKAL Lens connection: useful for relative strength, breakout proximity, and pullback depth observation.

### `distance_to_52w_low`

Definition: `adj_close / rolling_low_252d - 1`

Intuition: current adjusted close relative to the trailing one-year low.

JACKAL Lens connection: useful for recovery and trend repair observation.

### `ma_50`

Definition: trailing 50-day moving average of `adj_close`.

Intuition: intermediate trend reference line.

JACKAL Lens connection: useful for trend-state and pullback-quality features.

### `ma_200`

Definition: trailing 200-day moving average of `adj_close`.

Intuition: long-term trend reference line.

JACKAL Lens connection: useful for broad trend regime observation.

### `price_vs_ma_50`

Definition: `adj_close / ma_50 - 1`

Intuition: current price distance from the 50-day moving average.

JACKAL Lens connection: useful for short-to-intermediate trend extension or pullback context.

### `price_vs_ma_200`

Definition: `adj_close / ma_200 - 1`

Intuition: current price distance from the 200-day moving average.

JACKAL Lens connection: useful for long-term regime and trend-state context.

### `avg_dollar_volume_60d`

Definition: trailing 60-day average of `adj_close * volume`.

Intuition: approximate recent dollar liquidity.

JACKAL Lens connection: useful for liquidity-aware research and avoiding fragile observations from thinly traded names.

## Research Boundary

These factors are raw research features. They require validation before use in any research conclusion:

- Information Coefficient and rank IC.
- Grouped forward returns.
- Walk-forward or out-of-sample testing.
- Robustness checks across sectors, regimes, market-cap buckets, and liquidity buckets.
- Data-quality checks for missing prices, corporate actions, stale symbols, and vendor revisions.

Passing factor calculation does not imply statistical support. These fields must not be displayed or described as recommendations.

## Lens-Based Candidate Features

The project also includes first-pass candidate feature engineering inspired by public market-research styles:

- Serenity Lens features are documented in [SERENITY_LENS.md](SERENITY_LENS.md).
- JACKAL Lens features are documented in [JACKAL_LENS.md](JACKAL_LENS.md).

These modules create transparent hypothesis-strength fields for research triage only. They are not composite alpha scores, buy/sell signals, timing recommendations, or evidence of statistical validity.
