# Risk Lifecycle

How a position moves through Sentinel's risk states from open through alert
to liquidation (or recovery).

## Stage 1: Healthy (HF ≥ 1.5)

The position is safe by a comfortable margin. The monitor polls every
30 seconds but emits no alerts.

UI badge: green dot, gauge needle in upper third.

## Stage 2: Warning (1.20 ≤ HF < 1.50)

Volatility-driven HF erosion has reached the warning threshold. The risk
engine logs the position to the alert queue but does not page yet — first-
detection alerts often resolve within minutes as price normalizes.

UI badge: amber pulse, gauge needle middle band.

A *cooldown* of 15 minutes is applied so a single oscillating position
doesn't fire the same alert repeatedly.

## Stage 3: Danger (1.05 ≤ HF < 1.20)

The position is one moderate move away from liquidation. The risk engine:

1. Fires a Telegram alert (if `ALERT_WEBHOOK` is configured)
2. Surfaces a "danger" badge on the dashboard with countdown
3. Logs the event to the indexer for post-mortem analysis

UI badge: red pulse, gauge needle in lower third with shake animation.

## Stage 4: Critical (HF < 1.05)

Liquidation is mechanically possible at any moment. The dashboard shows the
estimated `time_to_liquidation` derived from the HF trajectory of the past
4 hours. Any user action page is escalated to *priority* — wallet
disconnect prompts, mobile push, etc.

UI badge: red flash, gauge needle pinned bottom, full-width banner.

## Stage 5: Liquidated

The on-chain liquidation event was detected by the indexer. The position
is moved to the *historical* tab with the realized loss recorded.

The risk engine does NOT page on liquidation itself — at that point it's
too late. The page should have come at Stage 3.

## Recovery path

A position can move back UP the lifecycle when price recovers. Cooldowns
re-arm after 15 minutes of HF stability above the prior tier's threshold.
