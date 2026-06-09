# Data Schema

Research only. Not financial advice. No auto-trading.

This document defines the first data templates for stock-alpha-lab. These files support hypothesis tracking, supply-chain mapping, market-regime notes, and research-only position/risk constraints. They are not trading signals and do not contain validated factor results.

## Files

### `data/watchlists/supply_chain_map.csv`

Purpose: maps tickers to AI, semiconductor, optical, power, and related supply-chain themes inspired by Serenity Lens style hypothesis discovery.

Fields:

- `ticker`: Listed security ticker.
- `company`: Company name.
- `theme`: Broad research theme, such as AI Compute or AI Power.
- `layer`: Supply-chain layer or business category.
- `sub_layer`: More specific product, service, or infrastructure layer.
- `downstream_link`: Demand linkage to downstream customers, capex, or end markets.
- `bottleneck_type`: Hypothesized bottleneck category.
- `replaceability`: Research estimate of how replaceable the company or layer may be.
- `capacity_constraint`: Research estimate of supply or capacity tightness.
- `main_risk`: Main qualitative risk to track.

Manual fields in v1: all fields.

Potential future automation:

- `ticker`, `company`: from security master data.
- `theme`, `layer`, `sub_layer`: from maintained taxonomy plus text classification.
- `downstream_link`: from customer, segment, and capex datasets.
- `capacity_constraint`: from measured supply, backlog, pricing, utilization, or lead-time data.

### `data/watchlists/thesis_tracker.csv`

Purpose: tracks research hypotheses before they become factors. Creator styles can seed ideas, but evidence must come from measurable features and statistical validation.

Fields:

- `date`: Date when the thesis row was created or updated.
- `source_handle`: Origin handle or internal source name.
- `source_style`: One of `serenity`, `jackal`, or `manual`.
- `ticker`: Related ticker, ETF, or index proxy.
- `thesis_type`: Category of thesis, such as supply chain, market regime, or bottleneck.
- `thesis`: Short hypothesis statement.
- `why_now`: Reason the hypothesis is being tracked now.
- `catalyst`: Observable future event or data update to monitor.
- `invalidation`: Condition that would weaken or invalidate the thesis.
- `conviction`: Manual research confidence score from 1 to 5.
- `evidence_level`: Manual evidence maturity score from 1 to 5.

Manual fields in v1: all fields.

Potential future automation:

- `date`: update timestamp from workflow tools.
- `source_style`: validation against an allowed enum.
- `conviction` and `evidence_level`: constrained input controls, not model truth.
- `catalyst` and `invalidation`: linked to structured event calendars or validation reports.

### `data/watchlists/market_regime.csv`

Purpose: stores market-regime observations inspired by JACKAL Lens style market-tempo research. These rows are placeholders until replaced by measured regime features.

Fields:

- `date`: Observation date.
- `spy_trend`: SPY trend state.
- `qqq_trend`: QQQ trend state.
- `smh_trend`: SMH trend state.
- `market_volume_state`: Market volume or participation state.
- `ai_sector_state`: AI-related sector observation state.
- `risk_state`: Overall research risk-state label.
- `notes`: Free-text caveats and context.

Manual fields in v1: all fields.

Potential future automation:

- `spy_trend`, `qqq_trend`, `smh_trend`: from reproducible trend rules.
- `market_volume_state`: from volume and breadth data.
- `ai_sector_state`: from theme baskets and relative strength features.
- `risk_state`: from documented regime classification logic.

### `data/watchlists/position_rules.yaml`

Purpose: defines research-only constraints for future simulations and reporting. It must not be used for live orders, broker actions, or investment recommendations.

Fields:

- `research_only`: Must remain true.
- `not_financial_advice`: Must remain true.
- `no_auto_trading`: Must remain true.
- `max_single_position_pct`: Maximum single simulated research weight.
- `drawdown_comfort_test`: Research drawdown comfort check for simulated baskets.
- `entry_rules`: Requirements before a candidate can enter a research simulation.
- `avoid_rules`: Conditions that require exclusion or warning in research simulations.

Manual fields in v1: all fields.

Potential future automation:

- `drawdown_comfort_test`: connected to simulated drawdown reports.
- `entry_rules`: connected to validation workflow status.
- `avoid_rules`: connected to data-quality and evidence-quality checks.

## Manual Maintenance

In v1, all watchlist data is manually maintained. Manual values are allowed only as hypothesis metadata and research controls. They are not validated alpha, not factor values, and not trade instructions.

Manual fields that need extra care:

- `replaceability`
- `capacity_constraint`
- `conviction`
- `evidence_level`
- `risk_state`
- Free-text thesis, catalyst, invalidation, and notes fields

These fields should be reviewed regularly because they can encode stale assumptions.

## Future Automation Candidates

Future workflow automation can add:

- Security master validation.
- Enum validation for categorical fields.
- Date parsing and freshness checks.
- Links to data provenance metadata.
- Measured market-regime features.
- Factor-validation result links.
- Missing-data and stale-data warnings.

Automation must preserve the distinction between observed data, manual hypotheses, derived features, validation results, and interpretation.

## Data Quality Notes

- Do not fabricate missing values.
- Do not backfill manual thesis fields as if they were point-in-time facts.
- Track update dates and source context.
- Treat public commentary as idea discovery only.
- Validate allowed values for `source_style`, `conviction`, and `evidence_level`.
- Avoid using these templates directly in factor tests until timestamp safety and data provenance are defined.
- Keep raw downloaded data outside these watchlist templates.

## Compliance Boundary

These files are research templates. They must not be interpreted as buy, sell, hold, short, target-price, position-size, or execution instructions.
