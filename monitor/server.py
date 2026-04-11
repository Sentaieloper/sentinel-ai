"""Sentinel AI — FastAPI monitoring server.

Exposes demo DeFi position and alert data for the SvelteKit dashboard.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import time

app = FastAPI(title="Sentinel AI Monitor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Demo Data ────────────────────────────────────────────────────────────────

BOOT_TIME = time.time()

positions = [
    {
        "id": "pos-1",
        "protocol": "Kamino",
        "asset": "SOL/USDC",
        "healthFactor": 2.41,
        "collateral": 12500,
        "debt": 5200,
        "riskLevel": "Safe",
        "liquidationPrice": 89.50,
        "autoProtect": True,
        "lastChecked": "2m ago",
    },
    {
        "id": "pos-2",
        "protocol": "Drift",
        "asset": "ETH-PERP",
        "healthFactor": 1.35,
        "collateral": 8400,
        "debt": 6200,
        "riskLevel": "Warning",
        "liquidationPrice": 2150.00,
        "autoProtect": False,
        "lastChecked": "1m ago",
    },
    {
        "id": "pos-3",
        "protocol": "Marinade",
        "asset": "mSOL",
        "healthFactor": 3.15,
        "collateral": 24800,
        "debt": 7900,
        "riskLevel": "Safe",
        "liquidationPrice": 0,
        "autoProtect": True,
        "lastChecked": "30s ago",
    },
    {
        "id": "pos-4",
        "protocol": "Kamino",
        "asset": "JitoSOL/SOL",
        "healthFactor": 1.08,
        "collateral": 3400,
        "debt": 3150,
        "riskLevel": "Critical",
        "liquidationPrice": 142.10,
        "autoProtect": False,
        "lastChecked": "10s ago",
    },
    {
        "id": "pos-5",
        "protocol": "Drift",
        "asset": "SOL-PERP",
        "healthFactor": 1.72,
        "collateral": 15600,
        "debt": 9100,
        "riskLevel": "Warning",
        "liquidationPrice": 128.40,
        "autoProtect": True,
        "lastChecked": "45s ago",
    },
]

alerts = [
    {
        "id": "alt-1",
        "type": "LIQUIDATION_IMMINENT",
        "protocol": "Kamino",
        "position": "JitoSOL/SOL",
        "message": "Health factor dropped below 1.10 — liquidation within ~15 minutes at current rate",
        "healthFactor": 1.08,
        "timestamp": "10 seconds ago",
        "severity": "Critical",
    },
    {
        "id": "alt-2",
        "type": "HEALTH_DECLINING",
        "protocol": "Drift",
        "position": "ETH-PERP",
        "message": "Position approaching warning zone — health factor 1.35 and declining",
        "healthFactor": 1.35,
        "timestamp": "2 minutes ago",
        "severity": "Warning",
    },
    {
        "id": "alt-3",
        "type": "AUTO_PROTECT",
        "protocol": "Kamino",
        "position": "JitoSOL/SOL",
        "message": "Auto-protect triggered: added 200 USDC collateral to prevent liquidation",
        "healthFactor": 1.08,
        "timestamp": "15 minutes ago",
        "severity": "Safe",
    },
    {
        "id": "alt-4",
        "type": "HEALTH_RECOVERED",
        "protocol": "Drift",
        "position": "SOL-PERP",
        "message": "Health factor recovered from 1.45 to 1.72 after price improvement",
        "healthFactor": 1.72,
        "timestamp": "1 hour ago",
        "severity": "Safe",
    },
    {
        "id": "alt-5",
        "type": "HEALTH_DECLINING",
        "protocol": "Kamino",
        "position": "SOL/USDC",
        "message": "Gradual health factor decline detected — dropped from 2.80 to 2.41 in 6 hours",
        "healthFactor": 2.41,
        "timestamp": "6 hours ago",
        "severity": "Warning",
    },
    {
        "id": "alt-6",
        "type": "LIQUIDATION_IMMINENT",
        "protocol": "Drift",
        "position": "ETH-PERP",
        "message": "Margin ratio approaching maintenance threshold — add collateral or reduce position",
        "healthFactor": 1.35,
        "timestamp": "8 hours ago",
        "severity": "Critical",
    },
    {
        "id": "alt-7",
        "type": "AUTO_PROTECT",
        "protocol": "Marinade",
        "position": "mSOL",
        "message": "Auto-protect standing by — position healthy at HF 3.15",
        "healthFactor": 3.15,
        "timestamp": "12 hours ago",
        "severity": "Safe",
    },
    {
        "id": "alt-8",
        "type": "HEALTH_RECOVERED",
        "protocol": "Kamino",
        "position": "SOL/USDC",
        "message": "Position recovered after SOL price rebound — HF stabilised at 2.41",
        "healthFactor": 2.41,
        "timestamp": "1 day ago",
        "severity": "Safe",
    },
]


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health")
def healthcheck():
    uptime_seconds = time.time() - BOOT_TIME
    uptime_pct = min(99.97, 99.0 + (uptime_seconds / 86400) * 0.97)
    return {"status": "monitoring", "uptime": round(uptime_pct, 2)}


@app.get("/api/stats")
def dashboard_stats():
    totalCollateral = sum(p["collateral"] for p in positions)
    totalDebt = sum(p["debt"] for p in positions)
    avgHealthFactor = round(
        sum(p["healthFactor"] for p in positions) / len(positions), 2
    )
    atRiskCount = sum(
        1 for p in positions if p["riskLevel"] in ("Critical", "Danger")
    )
    return {
        "totalCollateral": totalCollateral,
        "totalDebt": totalDebt,
        "avgHealthFactor": avgHealthFactor,
        "atRiskCount": atRiskCount,
        "positionCount": len(positions),
        "protocolCount": len(set(p["protocol"] for p in positions)),
    }


@app.get("/api/positions")
def list_positions():
    return positions


@app.get("/api/positions/{wallet}")
def wallet_positions(wallet: str):
    # Demo: return all positions regardless of wallet
    return positions


@app.get("/api/alerts")
def list_alerts(severity: Optional[str] = Query(None)):
    if severity:
        filtered = [a for a in alerts if a["severity"].lower() == severity.lower()]
        return filtered
    return alerts


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
