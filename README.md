# Sentinel AI

## Overview

Sentinel AI is an intelligent DeFi position monitoring system that detects liquidation risk before it happens. Using machine learning prediction models combined with real-time on-chain data analysis, Sentinel provides early warning alerts for DeFi positions across Solana lending protocols.

## Key Features

- **Real-Time Monitoring**: Continuous health factor tracking across supported protocols
- **ML-Powered Predictions**: XGBoost models trained on historical liquidation data
- **Risk Scoring**: Proprietary risk assessment combining multiple on-chain signals
- **Alert System**: Configurable thresholds with notification delivery

## Technology Stack

- **Smart Contracts**: Anchor (Rust) - Alert subscriptions and on-chain config
- **Frontend**: SvelteKit + Styled Components
- **ML Pipeline**: Python/FastAPI + XGBoost
- **Font**: IBM Plex Mono
- **Theme**: Dark military/tactical

## Development

```bash
# Deploy contracts
anchor build && anchor deploy

# ML service
cd ml && pip install -r requirements.txt && uvicorn main:app --reload

# Frontend
cd web && npm install && npm run dev
```

## Risk Disclaimer

Sentinel AI provides monitoring and predictions only. It does not execute trades or manage positions on your behalf. Predictions are probabilistic and should not be the sole basis for financial decisions. Always do your own research.

## License

MIT
