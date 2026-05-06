# Sentinel AI

## Overview

Sentinel AI is an intelligent DeFi position monitoring system that detects liquidation risk before it happens. Using machine learning prediction models combined with real-time on-chain data analysis, Sentinel provides early warning alerts for DeFi positions across Solana lending protocols.

## Key Features

- **Real-Time Monitoring**: Continuous health factor tracking across supported protocols
- **ML-Powered Predictions**: XGBoost models trained on historical liquidation data
- **Risk Scoring**: Proprietary risk assessment combining multiple on-chain signals
- **Alert System**: Configurable thresholds with notification delivery

## System Architecture

- **Smart Contracts**: Anchor (Rust) - Alert subscriptions and on-chain config
- **Frontend**: SvelteKit + Styled Components
- **ML Pipeline**: Python/FastAPI + XGBoost
- **Font**: IBM Plex Mono
- **Theme**: Dark military/tactical

## Local Build

```bash
# Deploy contracts
anchor build && anchor deploy

# ML service
cd ml && pip install -r requirements.txt && uvicorn main:app --reload

# Frontend
cd web && npm install && npm run dev
```

## Live Deployment

A devnet instance of the monitor is reachable at **[sentinel-fi.vercel.app](https://sentinel-fi.vercel.app)**. The deployment runs the full pipeline — SvelteKit dashboard, FastAPI scoring service, and the on-chain Drift / Kamino / MarginFi readers — against Solana devnet RPC. Treat it as a reference instance for the read-only feature set; on-chain alert subscriptions require a connected devnet wallet.

## Risk Disclaimer

Sentinel AI provides monitoring and predictions only. It does not execute trades or manage positions on your behalf. Predictions are probabilistic and should not be the sole basis for financial decisions. Always do your own research.

The reference deployment described above is a devnet instance for evaluation purposes. **Do not rely on this deployment for real-money risk decisions.** Production deployments must run against an audited mainnet RPC, with model artifacts versioned and reproducibility documented per your firm's risk policy.

## License

Distributed under the MIT License. Refer to the [LICENSE](LICENSE) file at the repository root for full terms. The grant is provided strictly "as is" and without warranty of any kind; the limitations enumerated therein operate in concert with the Risk Disclaimer above and govern any operational, evaluative, or derivative use of this codebase.
