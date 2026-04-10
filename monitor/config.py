import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("ANCHOR_PROVIDER_URL", "https://api.devnet.solana.com")
PROGRAM_ID = os.getenv("PROGRAM_ID", "")
KEYPAIR_PATH = os.getenv("CRANK_KEYPAIR_PATH", "./crank-keypair.json")

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "30"))

RISK_THRESHOLDS = {
    "Safe": 8000,       # health factor > 0.8
    "Warning": 5000,    # health factor > 0.5
    "Danger": 3000,     # health factor > 0.3
    "Critical": 0,      # below 0.3
}

ALERT_COOLDOWN_SECONDS = 600  # Don't re-alert for same position within 10 min


def load_keypair_bytes(path: str) -> bytes:
    resolved = Path(path).expanduser()
    with open(resolved, "r") as fh:
        data = json.load(fh)
    return bytes(data[:64])
