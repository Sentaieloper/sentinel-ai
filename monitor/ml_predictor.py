"""
ML Predictor — Sentinel AI

Heuristic-based liquidation time estimator.
Uses health factor thresholds to predict approximate time
until liquidation. Replace with XGBoost model when training
data is available.
"""


def predict_liquidation_time(health_factor: float, features: list[float]) -> float:
    """Predict estimated minutes until liquidation based on health factor.

    Args:
        health_factor: Current health factor as a decimal (e.g. 1.5 = 150%).
        features: Reserved for future ML model features (unused in heuristic mode).

    Returns:
        Estimated minutes until liquidation. float('inf') if position is safe.
    """
    if health_factor < 0.01:
        return 5.0        # Critical: ~5 min, likely already being liquidated
    elif health_factor < 0.05:
        return 15.0       # Severe: ~15 min
    elif health_factor < 0.1:
        return 60.0       # Danger: ~1 hour
    elif health_factor < 0.5:
        return 360.0      # Warning: ~6 hours
    elif health_factor < 1.0:
        return 1440.0     # Low: ~1 day
    elif health_factor < 1.2:
        return 4320.0     # Moderate: ~3 days
    else:
        return float('inf')  # Safe: no liquidation expected
