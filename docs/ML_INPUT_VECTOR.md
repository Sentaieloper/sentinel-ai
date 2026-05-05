# ML input vector

The risk classifier consumes a 7-dimensional feature vector for each open
position. This document is the canonical reference for what each dimension
means, where it comes from, and the valid range.

## Feature schema

| # | Feature                  | Source                          | Type    | Range                  | Notes                                       |
|---|--------------------------|---------------------------------|---------|------------------------|---------------------------------------------|
| 0 | `health_factor`          | on-chain (program state)        | f64     | (0, ∞)                 | Liquidation at 1.0; warning at 1.5          |
| 1 | `leverage`               | derived (debt / collateral_USD) | f64     | [1.0, 10.0]            | Capped at 10× regardless of protocol max    |
| 2 | `collateral_usd`         | Pyth (asset price × balance)    | f64     | [0, 10⁹]               | Sum across collateral assets                |
| 3 | `debt_usd`               | Pyth (debt-token price × debt)  | f64     | [0, 10⁹]               | Sum across borrows                          |
| 4 | `protocol_id`            | enum                            | i8      | {0,1,2}                | 0=Marinade, 1=Kamino, 2=Marginfi            |
| 5 | `volatility_proxy`       | 24h Pyth high-low / mid         | f64     | [0, 1]                 | Asset-volatility surrogate                  |
| 6 | `time_to_liquidation_h`  | derived (HF trajectory)         | f64     | [0, 720]               | Linear extrapolation of HF over last 4h     |

## Inference path

1. `monitor/server.py` polls `chain_reader/readers/{kamino,marinade,marginfi}.js`
2. Raw position struct → `derive_features()` → 7-tuple
3. `models/health_xgb_v3.json` (XGBoost) → probability of liquidation in 24h
4. Probability bucket → severity → alert

## Versioning

Feature shape is locked at v3. If you add a feature:
- bump model name to `health_xgb_v4`
- update this table and `derive_features()`
- ship a fallback that maps v4 → v3 by averaging the new feature out

## Sanity checks

The risk-engine logs a warning if any feature is outside its declared range.
For new feeds, run `python scripts/feature_audit.py --window 24h` to verify
distributions before retraining.
