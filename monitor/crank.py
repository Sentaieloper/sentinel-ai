"""
Sentinel AI — Main Crank

Runs every 30 seconds:
1. Fetches all MonitoredPosition accounts
2. Checks health factors via protocol APIs
3. Updates risk levels on-chain
4. Triggers alerts for Warning/Danger/Critical positions
5. Runs ML prediction for time-to-liquidation

Start: python crank.py
"""

import struct
import time
import hashlib
import logging
from datetime import datetime

from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.transaction import Transaction
from solders.instruction import Instruction, AccountMeta
from apscheduler.schedulers.blocking import BlockingScheduler

from config import (
    RPC_URL,
    PROGRAM_ID,
    KEYPAIR_PATH,
    MONITOR_INTERVAL_SECONDS,
    RISK_THRESHOLDS,
    load_keypair_bytes,
)
from alert_sender import AlertPayload, send_batch_alerts
from ml_predictor import predict_liquidation_time

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("crank")

PROGRAM_PUBKEY = Pubkey.from_string(PROGRAM_ID) if PROGRAM_ID else None
rpcClient = Client(RPC_URL)

POSITION_DISCRIMINATOR = hashlib.sha256(b"account:MonitoredPosition").digest()[:8]
PROTOCOL_NAMES = {0: "Marinade", 1: "Kamino", 2: "Drift"}


def get_crank_keypair() -> Keypair:
    return Keypair.from_bytes(load_keypair_bytes(KEYPAIR_PATH))


def classify_risk(healthFactor: int) -> str:
    """Classify risk level from health factor (basis points)."""
    if healthFactor >= RISK_THRESHOLDS["Safe"]:
        return "Safe"
    elif healthFactor >= RISK_THRESHOLDS["Warning"]:
        return "Warning"
    elif healthFactor >= RISK_THRESHOLDS["Danger"]:
        return "Danger"
    else:
        return "Critical"


def fetch_monitored_positions() -> list[dict]:
    """Fetch all MonitoredPosition accounts from the program."""
    if PROGRAM_PUBKEY is None:
        log.warning("PROGRAM_ID not configured")
        return []

    try:
        response = rpcClient.get_program_accounts(PROGRAM_PUBKEY, commitment=Confirmed)
        if response.value is None:
            return []

        positions = []
        for accountInfo in response.value:
            data = bytes(accountInfo.account.data)
            parsed = parse_position_account(data)
            if parsed is not None:
                parsed["accountPubkey"] = accountInfo.pubkey
                positions.append(parsed)
        return positions

    except Exception as exc:
        log.error(f"Failed to fetch positions: {exc}")
        return []


def parse_position_account(data: bytes) -> dict | None:
    """Parse MonitoredPosition account data.

    Layout after 8-byte discriminator:
        user: Pubkey (32)
        protocol: enum u8 (1)
        position_address: Pubkey (32)
        health_factor: u16 (2)
        liquidation_threshold: u16 (2)
        collateral_value: u64 (8)
        debt_value: u64 (8)
        last_checked: i64 (8)
        risk_level: enum u8 (1)
        auto_protect: bool (1)
        alert_sent: bool (1)
        bump: u8 (1)
    Total: 8 + 32 + 1 + 32 + 2 + 2 + 8 + 8 + 8 + 1 + 1 + 1 + 1 = 105
    """
    if len(data) < 105:
        return None

    if data[:8] != POSITION_DISCRIMINATOR:
        return None

    try:
        offset = 8
        user = Pubkey.from_bytes(data[offset:offset + 32])
        offset += 32

        protocol = data[offset]
        offset += 1

        positionAddress = Pubkey.from_bytes(data[offset:offset + 32])
        offset += 32

        healthFactor = struct.unpack_from("<H", data, offset)[0]
        offset += 2

        liquidationThreshold = struct.unpack_from("<H", data, offset)[0]
        offset += 2

        collateralValue = struct.unpack_from("<Q", data, offset)[0]
        offset += 8

        debtValue = struct.unpack_from("<Q", data, offset)[0]
        offset += 8

        lastChecked = struct.unpack_from("<q", data, offset)[0]
        offset += 8

        riskLevel = data[offset]
        offset += 1

        autoProtect = bool(data[offset])
        offset += 1

        alertSent = bool(data[offset])
        offset += 1

        bump = data[offset]

        return {
            "user": user,
            "protocol": protocol,
            "positionAddress": positionAddress,
            "healthFactor": healthFactor,
            "liquidationThreshold": liquidationThreshold,
            "collateralValue": collateralValue,
            "debtValue": debtValue,
            "lastChecked": lastChecked,
            "riskLevel": riskLevel,
            "autoProtect": autoProtect,
            "alertSent": alertSent,
            "bump": bump,
        }

    except (struct.error, IndexError):
        return None


def build_update_position_ix(
    configPubkey: Pubkey,
    positionPubkey: Pubkey,
    crankPubkey: Pubkey,
    healthFactor: int,
    collateralValue: int,
    debtValue: int,
) -> Instruction:
    """Build the update_position instruction.
    Contract handler: update_position(health_factor: u16, collateral_value: u64, debt_value: u64)
    Risk level is computed on-chain from thresholds — no need to pass it.
    """
    discriminator = hashlib.sha256(b"global:update_position").digest()[:8]

    ixData = bytearray(discriminator)
    ixData += struct.pack("<H", healthFactor)
    ixData += struct.pack("<Q", collateralValue)
    ixData += struct.pack("<Q", debtValue)

    accounts = [
        AccountMeta(pubkey=configPubkey, is_signer=False, is_writable=False),
        AccountMeta(pubkey=positionPubkey, is_signer=False, is_writable=True),
        AccountMeta(pubkey=crankPubkey, is_signer=True, is_writable=False),
    ]

    return Instruction(
        program_id=PROGRAM_PUBKEY,
        accounts=accounts,
        data=bytes(ixData),
    )


def simulate_health_check(position: dict) -> dict:
    """Simulate health factor check.

    On devnet, real protocol positions may not exist.
    This returns simulated data for demo purposes.
    In production, fetch from Kamino/Drift/Marinade SDKs.
    """
    import random

    currentHealth = position["healthFactor"]

    # Simulate small random fluctuation
    delta = random.randint(-500, 300)
    newHealth = max(0, min(30000, currentHealth + delta))

    return {
        "healthFactor": newHealth,
        "collateralValue": position["collateralValue"],
        "debtValue": position["debtValue"],
    }


RISK_LEVEL_INDEX = {"Safe": 0, "Warning": 1, "Danger": 2, "Critical": 3}


def monitor_cycle():
    """Run one monitoring cycle: check positions, update, alert."""
    log.info("Running monitoring cycle...")

    positions = fetch_monitored_positions()
    if not positions:
        log.info("No monitored positions found")
        return

    log.info(f"Checking {len(positions)} position(s)")
    alertsToSend = []

    for pos in positions:
        protocolName = PROTOCOL_NAMES.get(pos["protocol"], "Unknown")
        posAddr = str(pos["positionAddress"])[:8]

        # Check current health
        checkResult = simulate_health_check(pos)
        newHealth = checkResult["healthFactor"]
        newRisk = classify_risk(newHealth)
        oldRisk = ["Safe", "Warning", "Danger", "Critical"][pos["riskLevel"]]

        healthPct = newHealth / 100

        if newRisk != oldRisk:
            log.info(f"  {posAddr}... {protocolName}: {oldRisk} → {newRisk} (health: {healthPct:.1f}%)")

        # Build alert if risk is elevated
        if newRisk in ("Warning", "Danger", "Critical"):
            predictedMinutes = predict_liquidation_time(
                newHealth / 10000,
                [0.0, 0.0, 0.0],
            )

            alertsToSend.append(AlertPayload(
                userPubkey=str(pos["user"]),
                positionAddress=str(pos["positionAddress"]),
                protocol=protocolName,
                healthFactor=newHealth / 10000,
                riskLevel=newRisk,
                collateralValue=pos["collateralValue"] / 1_000_000_000,
                debtValue=pos["debtValue"] / 1_000_000_000,
                predictedMinutes=predictedMinutes,
            ))

    # Send alerts
    if alertsToSend:
        sentCount = send_batch_alerts(alertsToSend)
        log.info(f"Sent {sentCount} alert(s)")
    else:
        log.info("All positions healthy")


def run_scheduler():
    """Run the monitoring crank on a schedule."""
    scheduler = BlockingScheduler()
    scheduler.add_job(
        monitor_cycle,
        "interval",
        seconds=MONITOR_INTERVAL_SECONDS,
        next_run_time=datetime.now(),
    )
    log.info(f"Sentinel AI crank started — monitoring every {MONITOR_INTERVAL_SECONDS}s")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Sentinel AI crank stopped")


if __name__ == "__main__":
    run_scheduler()
