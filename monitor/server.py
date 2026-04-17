"""Sentinel AI — FastAPI monitoring server.

Exposes demo DeFi position and alert data for the SvelteKit dashboard.
"""

import os
import re
import urllib.request
import urllib.error
import urllib.parse
import json
import uuid

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
import time

DRIFT_READER_URL = os.environ.get("DRIFT_READER_URL", "http://127.0.0.1:8002")
CHAIN_READER_URL = os.environ.get("CHAIN_READER_URL", "http://127.0.0.1:8003")
HERMES_URL = os.environ.get("HERMES_URL", "https://hermes.pyth.network")

PYTH_FEEDS = {
    "SOL": "0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d",
    "BTC": "0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43",
    "ETH": "0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",
}

MAINTENANCE_MARGIN = 0.05  # 5%
_price_cache: Dict[str, tuple[float, float]] = {}  # asset -> (price, fetched_at)
_paper_positions: Dict[str, List[Dict[str, Any]]] = {}  # wallet -> list


def fetch_pyth_price(asset: str) -> float:
    asset = asset.upper()
    feed = PYTH_FEEDS.get(asset)
    if not feed:
        raise ValueError(f"unsupported asset {asset}")

    cached = _price_cache.get(asset)
    now = time.time()
    if cached and now - cached[1] < 5:
        return cached[0]

    url = f"{HERMES_URL}/api/latest_price_feeds?ids%5B%5D={feed}&parsed=true"
    req = urllib.request.Request(url, headers={"User-Agent": "sentinel-ai/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
    except urllib.error.URLError as e:
        raise HTTPException(status_code=502, detail=f"Pyth fetch failed: {e}")
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Pyth fetch failed: HTTP {e.code}")

    if not data:
        raise HTTPException(status_code=502, detail="Pyth returned no price")
    price_obj = data[0]["price"]
    raw = int(price_obj["price"])
    expo = int(price_obj["expo"])
    price = raw * (10 ** expo)
    _price_cache[asset] = (price, now)
    return price


def is_valid_solana_address(addr: str) -> bool:
    return bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', addr))

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
    if not is_valid_solana_address(wallet):
        raise HTTPException(status_code=400, detail="Invalid Solana wallet address")
    # Demo: return all positions regardless of wallet
    return positions


@app.get("/api/alerts")
def list_alerts(
    severity: Optional[str] = Query(None),
    wallet: Optional[str] = Query(None),
):
    if wallet and not is_valid_solana_address(wallet):
        raise HTTPException(status_code=400, detail="Invalid Solana wallet address")
    if severity:
        filtered = [a for a in alerts if a["severity"].lower() == severity.lower()]
        return filtered
    return alerts


class AdvicePosition(BaseModel):
    protocol: str
    asset: str
    healthFactor: Optional[float] = None
    healthPercent: Optional[float] = None
    leverage: Optional[float] = None
    riskLevel: Optional[str] = None
    unrealizedPnl: Optional[float] = None
    direction: Optional[str] = None
    notional: Optional[float] = None


def advice_for_position(p: AdvicePosition) -> List[dict]:
    tips: List[dict] = []
    hf = p.healthFactor if p.healthFactor is not None else 0
    hp = p.healthPercent if p.healthPercent is not None else min(hf * 25, 100)
    lev = p.leverage or 0
    pnl = p.unrealizedPnl or 0

    if hf < 1.15:
        tips.append({
            "severity": "Critical",
            "title": "Liquidation imminent",
            "body": f"Health factor {hf:.2f}. Add collateral or close part of the position now to avoid liquidation.",
        })
    elif hf < 1.5:
        tips.append({
            "severity": "Warning",
            "title": "Buffer is thin",
            "body": f"Health {hf:.2f} — a 5-10% adverse move lands you in the danger zone. Consider trimming size or topping up margin.",
        })
    elif hf < 2.0:
        tips.append({
            "severity": "Warning",
            "title": "Monitor closely",
            "body": f"Health {hf:.2f}. You have room, but volatility could pull it lower fast. Keep an alert nearby.",
        })
    else:
        tips.append({
            "severity": "Safe",
            "title": "Position healthy",
            "body": f"Health {hf:.2f}. No immediate action needed.",
        })

    if lev >= 10:
        tips.append({
            "severity": "Warning",
            "title": "High leverage",
            "body": f"Running at {lev:.1f}x. Small moves amplify. Keep a tight stop or scale down.",
        })
    elif lev >= 5:
        tips.append({
            "severity": "Safe",
            "title": "Moderate leverage",
            "body": f"{lev:.1f}x is manageable but leaves less room for volatility — watch funding.",
        })

    if p.protocol.lower() == "drift" and p.direction in ("LONG", "SHORT"):
        if pnl < 0 and abs(pnl) > (p.notional or 0) * 0.2:
            tips.append({
                "severity": "Warning",
                "title": "Drawdown over 20%",
                "body": "Unrealized loss is already large. Re-check your thesis before adding.",
            })
        if pnl > 0 and (p.notional or 0) > 0 and pnl > p.notional * 0.3:
            tips.append({
                "severity": "Safe",
                "title": "Consider partial take-profit",
                "body": "Up 30%+ on notional. Locking part of it lowers variance on the remainder.",
            })

    return tips


@app.post("/api/advice")
def generate_advice(position: AdvicePosition):
    return {
        "asset": position.asset,
        "protocol": position.protocol,
        "tips": advice_for_position(position),
    }


@app.get("/api/positions/live/{wallet}")
def live_positions(wallet: str):
    if not is_valid_solana_address(wallet):
        raise HTTPException(status_code=400, detail="Invalid Solana wallet address")

    url = f"{DRIFT_READER_URL}/positions/{wallet}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            payload = json.loads(resp.read())
    except urllib.error.URLError as e:
        raise HTTPException(status_code=503, detail=f"Drift reader unavailable: {e}")

    positions = payload.get("positions", [])
    for pos in positions:
        pos["advice"] = advice_for_position(AdvicePosition(**{
            k: pos.get(k) for k in AdvicePosition.model_fields.keys()
        }))

    return {
        "hasAccount": payload.get("hasAccount", False),
        "positions": positions,
        "summary": payload.get("summary"),
    }


class OpenPaperPosition(BaseModel):
    wallet: str
    asset: Literal["SOL", "BTC", "ETH"]
    direction: Literal["LONG", "SHORT"]
    collateralUsd: float = Field(gt=0)
    leverage: float = Field(ge=1, le=20)


def evaluate_paper_position(p: Dict[str, Any]) -> Dict[str, Any]:
    current_price = fetch_pyth_price(p["asset"])
    entry = p["entryPrice"]
    collateral = p["collateralUsd"]
    leverage = p["leverage"]
    notional = collateral * leverage
    direction = p["direction"]

    base_size = notional / entry
    if direction == "LONG":
        pnl = (current_price - entry) * base_size
    else:
        pnl = (entry - current_price) * base_size

    equity = max(collateral + pnl, 0)
    margin_ratio = equity / notional if notional > 0 else 0
    health_factor = margin_ratio / MAINTENANCE_MARGIN if notional > 0 else 0
    health_pct = min(health_factor * 25, 100)

    if direction == "LONG":
        liq_price = entry * (1 - (1 - MAINTENANCE_MARGIN) / leverage)
    else:
        liq_price = entry * (1 + (1 - MAINTENANCE_MARGIN) / leverage)

    if health_factor >= 2.0:
        risk = "Safe"
    elif health_factor >= 1.5:
        risk = "Warning"
    elif health_factor >= 1.15:
        risk = "Danger"
    else:
        risk = "Critical"

    advice_tips = advice_for_position(AdvicePosition(
        protocol="Sentinel",
        asset=f"{p['asset']}-PERP",
        healthFactor=round(health_factor, 2),
        healthPercent=round(health_pct, 1),
        leverage=leverage,
        riskLevel=risk,
        direction=direction,
        notional=notional,
        unrealizedPnl=pnl,
    ))

    return {
        "id": p["id"],
        "protocol": "Sentinel",
        "asset": f"{p['asset']}-PERP",
        "direction": direction,
        "baseSize": round(base_size, 6),
        "collateral": round(collateral, 2),
        "notional": round(notional, 2),
        "entryPrice": round(entry, 4),
        "oraclePrice": round(current_price, 4),
        "liquidationPrice": round(liq_price, 4),
        "unrealizedPnl": round(pnl, 2),
        "leverage": leverage,
        "healthFactor": round(health_factor, 2),
        "healthPercent": round(health_pct, 1),
        "riskLevel": risk,
        "debt": round(max(notional - collateral - pnl, 0), 2),
        "openedAt": p["openedAt"],
        "lastChecked": "just now",
        "source": "sentinel-paper",
        "advice": advice_tips,
    }


class EvaluateRequest(BaseModel):
    id: str
    asset: Literal["SOL", "BTC", "ETH"]
    direction: Literal["LONG", "SHORT"]
    collateralUsd: float
    leverage: float
    entryPrice: float
    openedAt: int
    source: str = "sentinel-onchain"


@app.post("/api/sentinel/evaluate")
def sentinel_evaluate(body: EvaluateRequest):
    payload = {
        "id": body.id,
        "asset": body.asset,
        "direction": body.direction,
        "collateralUsd": body.collateralUsd,
        "leverage": body.leverage,
        "entryPrice": body.entryPrice,
        "openedAt": body.openedAt,
    }
    evaluated = evaluate_paper_position(payload)
    evaluated["source"] = body.source
    return evaluated


@app.post("/api/paper/open")
def paper_open(body: OpenPaperPosition):
    if not is_valid_solana_address(body.wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    entry = fetch_pyth_price(body.asset)
    pos = {
        "id": f"paper-{uuid.uuid4().hex[:8]}",
        "asset": body.asset,
        "direction": body.direction,
        "collateralUsd": body.collateralUsd,
        "leverage": body.leverage,
        "entryPrice": entry,
        "openedAt": int(time.time()),
    }
    _paper_positions.setdefault(body.wallet, []).append(pos)
    return evaluate_paper_position(pos)


@app.get("/api/paper/positions/{wallet}")
def paper_list(wallet: str):
    if not is_valid_solana_address(wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    positions = _paper_positions.get(wallet, [])
    return [evaluate_paper_position(p) for p in positions]


@app.post("/api/paper/close/{position_id}")
def paper_close(position_id: str, wallet: str = Query(...)):
    if not is_valid_solana_address(wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    bucket = _paper_positions.get(wallet, [])
    for i, p in enumerate(bucket):
        if p["id"] == position_id:
            evaluated = evaluate_paper_position(p)
            bucket.pop(i)
            return {"closed": True, "position": evaluated}
    raise HTTPException(status_code=404, detail="position not found")


@app.get("/api/pyth/{asset}")
def pyth_snapshot(asset: str):
    asset = asset.upper()
    if asset not in PYTH_FEEDS:
        raise HTTPException(status_code=400, detail="unsupported asset")
    return {"asset": asset, "price": fetch_pyth_price(asset), "fetchedAt": int(time.time())}


def lending_advice(collateral: float, debt: float, hf: float, protocol: str) -> List[dict]:
    tips: List[dict] = []
    if debt <= 0:
        tips.append({
            "severity": "Safe",
            "title": "Supply only",
            "body": f"Supplied ${collateral:.0f} on {protocol}. No debt, position cannot be liquidated.",
        })
        return tips
    if hf < 1.1:
        tips.append({"severity": "Critical", "title": "Liquidation imminent",
                     "body": f"Health factor {hf:.2f}. Repay part of your debt or add collateral now."})
    elif hf < 1.3:
        tips.append({"severity": "Warning", "title": "Low buffer",
                     "body": f"HF {hf:.2f} — close to liquidation zone. Keep an eye on collateral-asset price."})
    elif hf < 2.0:
        tips.append({"severity": "Warning", "title": "Monitor closely",
                     "body": f"HF {hf:.2f}. Healthy but watch market moves; a -10% on collateral pushes you toward danger."})
    else:
        tips.append({"severity": "Safe", "title": "Healthy borrow",
                     "body": f"HF {hf:.2f}. Comfortable margin."})
    if collateral > 0 and debt / max(collateral, 1) > 0.7:
        tips.append({"severity": "Warning", "title": "High utilization",
                     "body": "Loan-to-value above 70%. Consider de-risking."})
    return tips


def staking_advice(asset: str, balance: float, sol_equiv: float) -> List[dict]:
    return [{
        "severity": "Safe",
        "title": "Liquid staking position",
        "body": f"{balance:.4f} {asset} ≈ {sol_equiv:.4f} SOL. Accruing staking yield. Can be unstaked or swapped instantly via Marinade instant-unstake pool.",
    }]


def wallet_advice(asset: str, balance: float) -> List[dict]:
    if asset == "SOL" and balance < 0.05:
        return [{"severity": "Warning", "title": "Low SOL",
                 "body": "Balance below 0.05 SOL. You may not be able to pay transaction fees soon."}]
    return [{"severity": "Safe", "title": "Wallet balance",
             "body": f"{balance:.4f} {asset} sitting in the wallet, ready to deploy."}]


def enrich_chain_position(p: Dict[str, Any]) -> Dict[str, Any]:
    src = p.get("source")
    if src in ("kamino", "marginfi"):
        p.setdefault("advice", lending_advice(
            p.get("collateral", 0) or 0,
            p.get("debt", 0) or 0,
            p.get("healthFactor", 0) or 0,
            p.get("protocol", "lending"),
        ))
    elif src == "marinade":
        p.setdefault("advice", staking_advice(
            p.get("asset", "mSOL"),
            p.get("balance", 0) or 0,
            p.get("solEquivalent", 0) or 0,
        ))
    elif src in ("native", "spl"):
        p.setdefault("advice", wallet_advice(p.get("asset", ""), p.get("balance", 0) or 0))
    return p


@app.get("/api/positions/chain/{wallet}")
def chain_positions(wallet: str):
    if not is_valid_solana_address(wallet):
        raise HTTPException(status_code=400, detail="Invalid Solana wallet address")

    url = f"{CHAIN_READER_URL}/all/{wallet}"
    req = urllib.request.Request(url, headers={"User-Agent": "sentinel-ai/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
    except urllib.error.URLError as e:
        raise HTTPException(status_code=503, detail=f"chain_reader unavailable: {e}")

    enriched = []
    errors = []
    for block in payload.get("results", []):
        if block.get("error"):
            errors.append({"protocol": block.get("protocol"), "error": block["error"]})
        for pos in block.get("positions", []) or []:
            enriched.append(enrich_chain_position(pos))
    return {"wallet": wallet, "positions": enriched, "errors": errors}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
