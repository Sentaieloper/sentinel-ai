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
    """Resolve a Solana CLI keypair into raw secret bytes.

    Order of resolution:
      1. CRANK_KEYPAIR_JSON env (Railway-friendly inline JSON; tolerates
         missing brackets when pasted via dashboards that strip them).
      2. Filesystem path (developer machine, default ./crank-keypair.json).
    """
    inline = os.environ.get("CRANK_KEYPAIR_JSON", "").strip()
    if inline:
        try:
            payload = json.loads(inline)
        except json.JSONDecodeError:
            inner = inline.lstrip("[(").rstrip(")]").strip()
            try:
                payload = [int(x) for x in inner.split(",") if x.strip()]
            except ValueError as e:
                raise ValueError(f"malformed CRANK_KEYPAIR_JSON: {e}") from e
        if not isinstance(payload, list) or len(payload) < 64:
            raise ValueError("CRANK_KEYPAIR_JSON expected >=64-byte int array")
        return bytes(payload[:64])

    keyfile = Path(path).expanduser().resolve()
    if not keyfile.is_file():
        raise FileNotFoundError(
            f"keypair file not found: {keyfile} (and CRANK_KEYPAIR_JSON not set)"
        )
    payload = json.loads(keyfile.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or len(payload) < 64:
        raise ValueError(f"malformed keypair at {keyfile} (expected >=64-byte array)")
    return bytes(payload[:64])
