# Multi-Market AI Research Plan

Research only. Not financial advice. No auto-trading.

This document describes the planned upgrade path for stock-alpha-lab from a single-market research scaffold into a local-first, multi-market AI factor research platform. It is an architecture plan only. It does not implement data downloads, model changes, UI pages, or AI API calls.

## Current System State

stock-alpha-lab already has a src-layout Python project with reusable modules for:

- Watchlist and thesis data loading.
- Prototype price downloads and normalized OHLCV storage.
- Price factor engineering.
- Serenity Lens and JACKAL Lens candidate factor engineering.
- Forward-return labels.
- IC analysis.
- Quantile return analysis.
- Walk-forward validation.
- Ridge and logistic walk-forward model skeletons.
- A minimal Streamlit interface.

The current system is still research-first. It does not place orders, route orders, manage accounts, or provide investment advice. Existing outputs should remain framed as hypotheses, statistical diagnostics, missing-data warnings, and research states.

## Target System

The target platform should support three stock markets:

- `US`: United States listed equities and ETFs.
- `HK`: Hong Kong listed equities and market proxies.
- `CN_A`: mainland China A-share equities and market proxies.

For each market, the platform should let a user enter a ticker, load or fetch real data through a configured provider, run reusable factor modules, evaluate available statistical support, and produce a structured research explanation.

The output should separate:

- Structured input data.
- Derived factor values.
- Statistical validation results.
- Model outputs.
- AI explanation text.
- Missing-data items.
- Risk warnings.
- Research conclusion state.

AI-generated explanations must never be treated as facts. They can only explain the structured data and research diagnostics supplied to them.

## Three-Market UI

The Streamlit app should evolve into three market-specific experiences:

- US Market Research.
- Hong Kong Market Research.
- A-Share Market Research.

Each market page should collect:

- Ticker.
- Data provider.
- Optional AI explanation toggle.

Each page should show the same research tabs:

- Overview.
- Serenity Lens.
- JACKAL Lens.
- Price Factors.
- Statistical Support.
- AI Explanation.
- Risks.

Every page must display:

```text
Research only. Not financial advice. No auto-trading.
```

The UI should not infer an action from the research state. It should present evidence, uncertainty, and missing-data context.

## Market Configuration

A market configuration module should define reusable market metadata rather than hardcoding benchmark or currency logic in business modules.

Planned fields:

- `market_code`.
- `market_name`.
- `ticker_format_examples`.
- `default_benchmarks`.
- `data_provider_priority`.
- `currency`.
- `timezone`.
- `trading_calendar_name`.

Initial market examples:

| Market | Example Tickers | Default Benchmarks | Currency | Timezone |
| --- | --- | --- | --- | --- |
| `US` | `NVDA`, `MU`, `AVGO`, `VST` | `SPY`, `QQQ`, `SMH` | `USD` | `America/New_York` |
| `HK` | `0700.HK`, `0981.HK`, `1810.HK` | configurable HSI or ETF proxies | `HKD` | `Asia/Hong_Kong` |
| `CN_A` | `300750.SZ`, `688256.SH`, `002371.SZ` | CSI and ChiNext proxies | `CNY` | `Asia/Shanghai` |

Benchmark selection must come from market configuration, not from factor or analyzer business logic.

## Data Source Layer

The data source layer should become provider-based and pluggable. Every provider should return the same normalized price schema:

```text
date,ticker,market,open,high,low,close,adj_close,volume,currency,source
```

Planned provider abstraction:

- `provider_base.py`: shared provider protocol or abstract base class.
- `csv_provider.py`: local CSV fallback for every market.
- `provider_registry.py`: provider lookup by market and provider name.
- API provider skeletons for future paid data vendors.

Candidate provider families:

- US and HK: Tiingo, Polygon, Alpha Vantage, Interactive Brokers exports, manual CSV.
- CN_A: Tushare, AkShare, Wind, Choice, JoinQuant, RiceQuant, manual CSV.

The first implementation should include `CSVProvider`, one API provider skeleton, and registry wiring. It should not require paid credentials to run tests.

`scripts/update_prices.py` should eventually accept:

```powershell
python scripts/update_prices.py --market US --provider tiingo --tickers NVDA,MU --start 2020-01-01
python scripts/update_prices.py --market HK --provider csv --input data/external/hk_prices.csv
python scripts/update_prices.py --market CN_A --provider csv --input data/external/a_prices.csv
```

Missing vendor data must be reported as `missing_data`. The system must not fabricate prices, fundamentals, or market metadata.

## AI Provider Layer

The AI layer should explain structured research results, not create facts.

Planned module layout:

```text
src/stock_alpha_lab/ai/
  __init__.py
  provider_base.py
  prompt_templates.py
  explanation_engine.py
  mock_provider.py
```

Initial rules:

- If no AI credentials are configured, use a mock or rule-based provider.
- If credentials exist, future providers can call OpenAI, DeepSeek, Anthropic, or another configured API.
- AI output must cite the supplied factor values, thesis fields, statistical support, and missing-data items.
- AI output must include the research-only disclaimer.
- AI output must not invent company facts, financial data, statistical results, or market events.
- AI output must not include trade recommendation language.

Planned environment variables:

```text
AI_PROVIDER=
AI_API_KEY=
AI_MODEL=
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=
```

No AI provider should require credentials for local tests.

## Reusing Existing Factor Models

The current modules should be extended rather than rewritten.

Reusable modules:

- `price_factors.py`: momentum, volatility, moving averages, drawdown, 52-week position, and dollar volume.
- `serenity_factors.py`: supply-chain bottleneck hypothesis features.
- `jackal_factors.py`: relative strength, trend, pullback, and volatility context.
- `forward_returns.py`: future return labels.
- `ic_analysis.py`: rank IC diagnostics.
- `quantile_analysis.py`: grouped forward-return diagnostics.
- `walk_forward.py`: chronological split validation.
- Ridge and logistic model modules: sample-out prediction research skeletons.

Future changes should add optional `market` support while preserving backward compatibility for existing tests and US-first datasets.

## Serenity Lens Across Markets

Serenity Lens should remain a hypothesis source for supply-chain and industry-structure features. For multi-market support, the watchlist schema should include `market` so that a US ticker, HK ticker, and A-share ticker can coexist without ticker collision.

Core structured fields:

- Theme.
- Layer and sub-layer.
- Downstream link.
- Bottleneck type.
- Replaceability.
- Capacity constraint.
- Main risk.
- Thesis evidence level.
- Conviction.
- Thesis age.
- Dilution or capital-raising risk flag.

The `serenity_hypothesis_strength` field remains a transparent hypothesis-strength measure, not an investment score.

Market-specific considerations:

- US: AI compute, semiconductors, optical components, memory, power, and listed infrastructure proxies.
- HK: China internet, hardware supply chain, local liquidity, and Hong Kong-specific listing dynamics.
- CN_A: domestic semiconductor supply chain, power equipment, robotics, industrial policy sensitivity, and A-share liquidity structure.

Subjective commentary must be converted into documented, observable fields before it can enter research tables.

## JACKAL Lens Across Markets

JACKAL Lens should remain a hypothesis source for market tempo, relative strength, trend, pullback, and volatility context.

Core structured fields:

- Relative strength versus configured market benchmarks.
- 50/200 moving-average trend filter.
- 20-day pullback depth.
- Distance to key moving averages.
- Volatility risk bucket.
- Market regime context.
- Timing hypothesis strength.

The `jackal_timing_hypothesis_strength` field remains a timing-hypothesis measure, not a trade timing instruction.

Market-specific benchmark handling:

- US should use configured US benchmarks such as `SPY`, `QQQ`, and `SMH`.
- HK should use configured Hang Seng or Hong Kong ETF proxies.
- CN_A should use configured broad-market and growth-board proxies.

Benchmark logic must use market configuration so that factors do not mix incompatible market regimes.

## Multi-Market Statistical Validation

The research modules should be extended to preserve market boundaries:

- `factor_df` should optionally include `market`.
- `forward_return_df` should optionally include `market`.
- IC should group by `market + date + factor_name + horizon` when `market` exists.
- Quantile analysis should group by `market + date + factor_name` when `market` exists.
- Walk-forward validation should not train one market on another market unless an explicit cross-market experiment is documented.
- Market-specific benchmarks should be read from configuration.

Backward compatibility rule:

- If `market` is missing in legacy data, loaders should default to `US` where that is the safest interpretation of existing examples.

Validation outputs should report sample size, missing data, time coverage, and market coverage. Statistical support is not a guarantee of future performance.

## Single-Stock Analyzer Design

The planned analyzer should provide a single structured entry point:

```python
analyze_stock(
    ticker: str,
    market: str,
    data_dir: str | Path = "data",
    use_ai: bool = False,
) -> dict
```

Planned response shape:

```text
ticker
market
status
overview
serenity
jackal
price_factors
statistical_support
model_outputs
ai_explanation
risks
missing_data
research_conclusion
```

Allowed conclusion enums:

- `research_priority`: `HIGH`, `MEDIUM`, `LOW`, `AVOID_RESEARCH`.
- `signal_confidence`: `HIGH`, `MEDIUM`, `LOW`, `INSUFFICIENT_DATA`.
- `action_state`: `WATCH`, `WAIT_FOR_MORE_DATA`, `WAIT_PULLBACK`, `RESEARCH_ONLY`, `AVOID`.

These are research workflow states only. They must not imply an order, allocation, or personalized action.

## Watchlist Schema Upgrade

Existing watchlist files should become multi-market aware:

`data/watchlists/supply_chain_map.csv`:

```text
market,ticker,company,theme,layer,sub_layer,downstream_link,bottleneck_type,replaceability,capacity_constraint,main_risk
```

`data/watchlists/thesis_tracker.csv`:

```text
date,market,source_handle,source_style,ticker,thesis_type,thesis,why_now,catalyst,invalidation,conviction,evidence_level
```

Compatibility rules:

- If legacy files do not include `market`, loaders should add `market = US`.
- Tickers should be normalized carefully without damaging HK or A-share suffixes.
- Missing fields should raise clear validation errors.
- Missing data should remain missing unless a documented rule says otherwise.

## API Key Safety Strategy

Secrets must never be committed.

Required rules:

- `.env` stays ignored by git.
- `.env.example` can list variable names with empty values.
- API keys are read from environment variables or `.env`.
- Tests must pass without paid credentials.
- Providers must fail clearly when required credentials are missing.
- Logs and exceptions must not print secrets.
- No source file should contain hardcoded private keys, tokens, or paid-data endpoints.

## Development Roadmap

Recommended incremental order:

1. Multi-market architecture plan.
2. Multi-market watchlist schema and loader compatibility.
3. Market configuration module.
4. Data provider abstraction with CSV provider and registry.
5. AI provider abstraction with mock explanation provider.
6. Market-aware single-stock analyzer.
7. Three-market Streamlit pages or tabs.
8. Paid data provider integration after vendor selection.
9. Real AI provider integration after API selection.
10. Market-aware statistical validation enhancements.
11. Research report generation.
12. Robustness analysis by market, regime, sector, and liquidity bucket.

Every step should keep existing tests passing and should add focused tests for new behavior.

## Risks And Limits

Key risks:

- Data provider differences in adjustments, calendars, symbols, and survivorship.
- HK and A-share holidays, trading limits, suspensions, and liquidity constraints.
- Point-in-time errors in fundamentals, corporate actions, and thesis data.
- Creator-inspired hypotheses becoming subjective labels instead of testable features.
- AI explanations sounding more certain than the underlying evidence.
- Overfitting from repeated tests across markets, factors, and horizons.
- Benchmark mismatch across market regimes.
- Small samples for newer listings or sparse thematic watchlists.
- Missing data being misread as neutral evidence.

Required mitigations:

- Keep provenance and source fields visible.
- Preserve `missing_data` in analyzer output.
- Report sample size and validation coverage.
- Keep AI text separate from structured data and statistical support.
- Use walk-forward validation before describing any factor as research-supported.

Research only. Not financial advice.
