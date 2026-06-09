# Project Overview

stock-alpha-lab is a local-first quantitative research platform for studying stock-selection factors. Its purpose is to turn market narratives into testable alpha hypotheses, then evaluate them with reproducible statistics.

The platform is not an automated trading system and not an investment advice system.

## Mission

Build a research workflow that can answer:

- Which hypotheses deserve more research?
- Which features have statistical support?
- Which results are fragile, regime-dependent, stale, or data-limited?
- Which ideas should remain under observation or be rejected?

The project should help prioritize research, not tell anyone what to buy or sell.

## Inspiration Model

Public creator commentary can be useful for idea discovery, but it cannot be used as proof.

### Serenity Lens Inspired Hypotheses

Potential feature families:

- AI and semiconductor supply-chain bottleneck exposure.
- Upstream component and equipment constraints.
- CPO, HBM, InP, Neocloud, power infrastructure, and robotics theme exposure.
- Revenue, margin, backlog, and capex sensitivity to bottleneck themes when reliable data exists.
- Relative strength inside supply-chain groups.

### JACKAL Lens Inspired Hypotheses

Potential feature families:

- SPY, QQQ, and SMH trend state.
- Market pullback quality and recovery behavior.
- Relative strength versus benchmark and industry group.
- Volatility, breadth, liquidity, and drawdown context.
- Regime-aware position-comfort proxies for research simulation only.

These ideas must be converted into measurable features before testing.

## Research Lifecycle

1. Hypothesis definition.
2. Data sourcing and provenance checks.
3. Feature construction.
4. Bias controls and timestamp validation.
5. IC and rank IC analysis.
6. Grouped or quantile forward-return analysis.
7. Walk-forward or out-of-sample validation.
8. Robustness checks.
9. Research report generation.
10. Observation, revision, or rejection.

## Evidence Standards

A factor should not be marked as statistically supported until it has:

- Clear hypothesis and feature definition.
- Adequate sample size.
- Documented universe and forward-return horizon.
- Point-in-time or timestamp-safe inputs.
- IC/rank IC results.
- Grouped return results.
- Walk-forward or out-of-sample results.
- Robustness checks across regimes or relevant subgroups.
- Known risks and failure modes.

## Output Taxonomy

Allowed research states:

- Candidate: hypothesis is defined but not fully tested.
- Needs More Data: data is incomplete, sparse, stale, or unreliable.
- Watch: evidence is interesting but not strong enough.
- Statistically Supported: evidence passes the current validation standard.
- Rejected: evidence is weak, unstable, or contradicted by tests.

No state should imply a buy, sell, hold, short, target price, stop loss, or position size.

## Risk Controls

The platform must explicitly watch for:

- Look-ahead bias.
- Survivorship bias.
- Data revisions and point-in-time errors.
- Multiple testing and data snooping.
- Sector, size, liquidity, and beta concentration.
- Regime dependence.
- Overlapping forward-return labels.
- Transaction-cost sensitivity in portfolio-like research simulations.

## Local-First Design

The project should run locally by default. External services may be used for data access only when credentials are provided through environment variables or local configuration outside version control.

Secrets must never be committed.

## Future Architecture Direction

The likely future modules are:

- Data connectors with provenance metadata.
- Feature engineering pipelines.
- Factor validation utilities.
- Walk-forward experiment runners.
- Research report generation.
- Optional local UI for viewing evidence and observation states.

This overview intentionally avoids implementation details until the first research workflow is designed.

