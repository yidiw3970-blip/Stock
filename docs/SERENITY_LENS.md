# Serenity Lens

Research only. Not financial advice. No auto-trading.

Serenity Lens style research focuses on structural bottlenecks in AI and semiconductor supply chains. In this project, that perspective is used only as an alpha hypothesis source for feature engineering.

## Research Focus

Candidate themes include:

- AI compute platforms.
- HBM and memory constraints.
- Optical, CPO, and InP infrastructure.
- Custom ASIC and networking bottlenecks.
- Power, nuclear, grid, and data-center infrastructure.
- Robotics and other upstream components when measurable data exists.

These are research themes, not evidence. The project must not treat theme exposure as proof of future returns.

## Structured Candidate Features

`compute_serenity_factors` converts local watchlist data into transparent hypothesis features:

- `replaceability_numeric`: maps lower replaceability to higher bottleneck hypothesis strength.
- `capacity_constraint_numeric`: maps stronger capacity constraint to higher bottleneck hypothesis strength.
- `upstream_layer_numeric`: maps recognized upstream layers such as HBM, Optical, CPO, InP, Power, Nuclear, Grid, ASIC, Networking, and Memory.
- `evidence_level`: manually maintained evidence maturity from the thesis tracker.
- `conviction`: manually maintained research confidence from the thesis tracker.
- `thesis_age_days`: age of the latest thesis as of the requested date.
- `thesis_count`: number of timestamp-safe thesis rows available for the ticker.
- `dilution_risk_flag`: flags dilution, ATM, offering, share issuance, or equity raise language.
- `serenity_missing_reason`: records missing thesis data or unknown upstream layers.

## Hypothesis Strength

`serenity_hypothesis_strength` is a transparent hypothesis-strength feature, not a buy score.

Formula:

```text
0.25 * replaceability_numeric
+ 0.25 * capacity_constraint_numeric
+ 0.20 * upstream_layer_numeric
+ 0.15 * evidence_level_scaled
+ 0.15 * conviction_scaled
```

If dilution risk is detected, the result is multiplied by `0.85`.

Missing thesis evidence uses a neutral value for calculation and records the missing reason.

## Required Validation

This module does not establish whether any factor is useful. Later research must test:

- IC and rank IC.
- Grouped forward returns.
- Walk-forward or out-of-sample stability.
- Robustness across regimes, sectors, market-cap buckets, and liquidity buckets.
- Sensitivity to manual labels and stale theses.

## Risks

- Manual labels can encode subjective bias.
- Theme baskets can suffer from survivorship bias.
- Popular themes can become crowded.
- Small-cap and lower-liquidity names can distort apparent results.
- Dilution risk can change quickly.
- Public narrative attention is not statistical evidence.

These features must not be displayed or interpreted as buy, sell, hold, short, target-price, or position-size instructions.
