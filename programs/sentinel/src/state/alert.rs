use anchor_lang::prelude::*;

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum AlertType {
    Warning,
    Danger,
    Critical,
    Liquidated,
    Protected,
}

#[account]
#[derive(InitSpace)]
pub struct AlertLog {
    pub user: Pubkey,
    pub position: Pubkey,
    pub alert_type: AlertType,
    pub health_factor_at_alert: u16,
    pub predicted_liquidation_time: Option<i64>,
    #[max_len(128)]
    pub action_taken: Option<String>,
    pub created_at: i64,
    pub bump: u8,
}
