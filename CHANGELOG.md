# Changelog

## [0.4.6] — Documentation Pass

### Added
- ML Input Vector Documentation At docs/ML_INPUT_VECTOR.md With 7d Feature Schema
- Risk Threshold Env Vars Block In monitor/.env.example Mirror On-Chain Constants

### Notes
- Feature Shape Locked At v3 — Adding A Feature Now Requires Bumping Model Name

## [0.4.5] — Phase 4.5: Aggregator + Hardening

### Added
- Chain reader microservice that aggregates positions across Drift, Kamino, Solend
- Tactical radar landing page with mode badge (LIVE / DEMO)
- Phantom wallet adapter wired through SvelteKit stores
- LIVE / DEMO mode toggle for offline demo presentations

### Changed
- Access control hardened on `open_leveraged` instruction — signer + authority constraints made explicit
- ML predictor input vector documented and pinned to seven features
- Risk dashboard tightened on mobile, gauges stack vertically below 768px

### Fixed
- Health gauge animation timing softened from 800 ms to 450 ms with cubic-bezier easing
- Position aggregator no longer panics when a CPI returns an empty position list

## [0.4.0] — Phase 4: ML pipeline + FastAPI server

### Added
- XGBoost risk predictor with offline training pipeline
- FastAPI `/risk` and `/positions` endpoints with Pydantic schemas
- SvelteKit dashboard wired to FastAPI through fetch + SSE updates

## [0.3.0] — Phase 3: Anchor program

### Added
- `open_leveraged`, `close_leveraged`, `liquidate` instructions
- Position state account with health-factor + liquidation-threshold fields
- Custom error codes for under-collateralisation paths
