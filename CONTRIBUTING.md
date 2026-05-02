# Contributing

Welcome! Sentinel-AI is the on-chain health-monitor for Solana DeFi positions.
Below is the quick guide. For deeper background see `docs/`.

## Layout

```
.
├── programs/sentinel/         Anchor program — position registry + thresholds
├── monitor/                   FastAPI service — risk engine + chain reader
├── app/                       SvelteKit dashboard
└── docs/                      ML input vector, risk lifecycle, etc.
```

## Local Dev

### Anchor program

```sh
cd programs/sentinel
anchor build
anchor test
anchor deploy --provider.cluster devnet
```

### Monitor service

```sh
cd monitor
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in RPC + thresholds
uvicorn server:app --reload
```

### Dashboard

```sh
cd app
npm i
npm run dev
```

## Commit Style

Title Case, action-first verbs.

```
Add Health Factor Monitor
Implement ML Prediction Pipeline
Document Risk Threshold Env Vars
Bump CHANGELOG To 0.4.6 With Polish Pass Entries
```

Avoid passive doc-style titles ("Documentation Update") — prefer active
forms ("Document X For Y").

## Pull Requests

1. Branch from `main`: `feat/<topic>` / `fix/<id>` / `docs/<topic>`
2. Run `pytest monitor/ && cd app && npm run test` before pushing
3. PRs touching the program should include an `anchor test` run output
4. Include a "Risk Considerations" paragraph for any threshold or alert change

## Security

This software watches money. Treat any change to threshold logic, alert
delivery, or chain-reader parsing as security-relevant. CC `@security` on
PRs touching `monitor/risk_engine.py` or `programs/sentinel/src/state.rs`.

## Code Of Conduct

Be respectful in code reviews. Disagree on technical merit. Help newcomers.
