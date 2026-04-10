"""
Alert Sender — Sentinel AI

Sends alerts via Telegram when positions reach Warning/Danger/Critical
risk levels. Maintains a cooldown per position to avoid alert spam.

Triggered by the crank when health factors change.
"""

import time
import logging
from dataclasses import dataclass

import httpx

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    ALERT_COOLDOWN_SECONDS,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("alert_sender")

# Track last alert time per position to avoid spam
_alertCooldowns: dict[str, float] = {}

RISK_EMOJI = {
    "Safe": "🟢",
    "Warning": "🟡",
    "Danger": "🟠",
    "Critical": "🔴",
    "Liquidated": "💀",
}

PROTOCOL_NAMES = {0: "Marinade", 1: "Kamino", 2: "Drift"}


@dataclass
class AlertPayload:
    userPubkey: str
    positionAddress: str
    protocol: str
    healthFactor: float
    riskLevel: str
    collateralValue: float
    debtValue: float
    predictedMinutes: float


def should_send_alert(positionAddress: str) -> bool:
    """Check if enough time has passed since last alert for this position."""
    lastSent = _alertCooldowns.get(positionAddress, 0)
    return (time.time() - lastSent) > ALERT_COOLDOWN_SECONDS


def mark_alert_sent(positionAddress: str):
    """Record that an alert was just sent for this position."""
    _alertCooldowns[positionAddress] = time.time()


def format_telegram_message(alert: AlertPayload) -> str:
    """Format an alert as a Telegram message."""
    emoji = RISK_EMOJI.get(alert.riskLevel, "⚠️")
    healthPct = alert.healthFactor * 100

    lines = [
        f"{emoji} *SENTINEL AI — {alert.riskLevel.upper()} ALERT*",
        "",
        f"*Protocol:* {alert.protocol}",
        f"*Health Factor:* {healthPct:.1f}%",
        f"*Collateral:* {alert.collateralValue:.2f} SOL",
        f"*Debt:* {alert.debtValue:.2f} SOL",
    ]

    if alert.predictedMinutes > 0:
        if alert.predictedMinutes < 60:
            lines.append(f"*Est. Liquidation:* {alert.predictedMinutes:.0f} min")
        else:
            hours = alert.predictedMinutes / 60
            lines.append(f"*Est. Liquidation:* {hours:.1f} hours")

    if alert.riskLevel == "Critical":
        lines.append("")
        lines.append("⚠️ _Immediate action recommended: add collateral or close position_")
    elif alert.riskLevel == "Danger":
        lines.append("")
        lines.append("_Consider adding collateral to improve health factor_")

    lines.append("")
    lines.append(f"`{alert.positionAddress[:16]}...`")

    return "\n".join(lines)


def send_telegram_alert(alert: AlertPayload) -> bool:
    """Send an alert message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram not configured — skipping alert")
        return False

    if not should_send_alert(alert.positionAddress):
        log.info(f"Alert cooldown active for {alert.positionAddress[:8]}...")
        return False

    message = format_telegram_message(alert)

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = httpx.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("ok"):
            mark_alert_sent(alert.positionAddress)
            log.info(f"Alert sent for {alert.positionAddress[:8]}... ({alert.riskLevel})")
            return True
        else:
            log.error(f"Telegram API error: {result.get('description', 'unknown')}")
            return False

    except Exception as exc:
        log.error(f"Failed to send Telegram alert: {exc}")
        return False


def send_batch_alerts(alerts: list[AlertPayload]) -> int:
    """Send multiple alerts, returns count of successfully sent."""
    sentCount = 0
    for alert in alerts:
        if alert.riskLevel == "Safe":
            continue
        if send_telegram_alert(alert):
            sentCount += 1
    return sentCount


def clear_cooldowns():
    """Clear all alert cooldowns (for testing)."""
    _alertCooldowns.clear()
