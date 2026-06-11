# Data Sources

Research only. Not financial advice. No auto-trading.

This document describes external data connectors used by stock-alpha-lab. The first connector is a yfinance-based research prototype for historical OHLCV prices.

## yfinance Prototype

Purpose:

- Download historical OHLCV data for local research prototypes.
- Normalize single-ticker history into a consistent schema.
- Save local CSV files under `data/raw/`.

Boundary:

- yfinance is used as a convenient research/prototype package.
- The project does not claim yfinance is an official Yahoo data source.
- The connector must not be used for automated trading, broker execution, or investment advice.
- Downloaded prices must not be treated as a live-trading guarantee.

## Normalized Price Fields

The normalized output schema is:

- `date`: Trading date or timestamp converted to pandas datetime with timezone removed.
- `ticker`: Uppercase ticker symbol.
- `open`: Open price.
- `high`: High price.
- `low`: Low price.
- `close`: Close price.
- `adj_close`: Adjusted close when provided; otherwise filled from `close`.
- `volume`: Reported volume.

Default output path:

```text
data/raw/prices.csv
```

## Risks And Limitations

- Data can be delayed, revised, missing, or inconsistent across tickers.
- Adjusted prices can differ across vendors and adjustment policies.
- Delistings, symbol changes, corporate actions, and survivorship bias require additional handling.
- Network failures and provider-side rate limits can interrupt downloads.
- The data is not point-in-time certified.
- A successful download does not validate any factor or thesis.

## Future Replacement Options

For more formal research workflows, this connector can be replaced or supplemented by vendors such as:

- Polygon
- Tiingo
- Alpha Vantage
- Nasdaq Data Link
- Direct exchange or licensed institutional feeds

Any replacement should document license terms, coverage, adjustment methodology, point-in-time support, refresh policy, and failure behavior.
