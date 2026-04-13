pub const CONFIG_SEED: &[u8] = b"sentinel_config";
pub const POSITION_SEED: &[u8] = b"position";
pub const SUBSCRIPTION_SEED: &[u8] = b"subscription";
pub const ALERT_SEED: &[u8] = b"alert";

pub const FREE_TIER_MAX_POSITIONS: u8 = 3;
pub const PRO_TIER_MAX_POSITIONS: u8 = 50;

pub const HEALTH_FACTOR_DECIMALS: u16 = 10_000; // 10000 = 1.0
pub const WARNING_THRESHOLD: u16 = 15_000;       // 1.5
pub const DANGER_THRESHOLD: u16 = 12_000;        // 1.2
pub const CRITICAL_THRESHOLD: u16 = 10_500;      // 1.05
