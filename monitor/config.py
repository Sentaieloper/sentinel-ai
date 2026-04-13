# Sentinel AI — monitor configuration
import os
import sys
import json
from pathlib import Path


def _load():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

_load()


def _require(var, fallback=None):
    v = os.environ.get(var, fallback)
    if not v:
        print(f"[sentinel] warning: {var} not set", file=sys.stderr)
    return v or ''


RPC_URL = os.environ.get("ANCHOR_PROVIDER_URL", "https://api.devnet.solana.com")
PROGRAM_ID = _require("PROGRAM_ID")
KEYPAIR_PATH = os.environ.get("CRANK_KEYPAIR_PATH", "./crank-keypair.json")

HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY", "")
BIRDEYE_API_KEY = os.environ.get("BIRDEYE_API_KEY", "")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

MONITOR_INTERVAL_SECONDS = int(os.environ.get("MONITOR_INTERVAL_SECONDS", "30"))

RISK_THRESHOLDS = {
    "Safe": 15000,      # health factor >= 1.5
    "Warning": 12000,   # health factor >= 1.2
    "Danger": 10500,    # health factor >= 1.05
    "Critical": 0,      # below 1.05
}

ALERT_COOLDOWN_SECONDS = 600  # Don't re-alert for same position within 10 min


def load_keypair_bytes(path: str) -> bytes:
    resolved = Path(path).expanduser()
    with open(resolved, "r") as fh:
        data = json.load(fh)
    return bytes(data[:64])
