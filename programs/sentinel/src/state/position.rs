use anchor_lang::prelude::*;

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum SupportedProtocol {
    Marinade,
    Kamino,
    Drift,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum RiskLevel {
    Safe,
    Warning,
    Danger,
    Critical,
}

#[account]
#[derive(InitSpace)]
pub struct MonitoredPosition {
    pub user: Pubkey,
    pub protocol: SupportedProtocol,
    pub position_address: Pubkey,
    pub health_factor: u16,
    pub liquidation_threshold: u16,
    pub collateral_value: u64,
    pub debt_value: u64,
    pub last_checked: i64,
    pub risk_level: RiskLevel,
    pub auto_protect: bool,
    pub alert_sent: bool,
    pub bump: u8,
}
