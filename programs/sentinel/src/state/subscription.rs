use anchor_lang::prelude::*;

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum SubscriptionTier {
    Free,
    Pro,
}

#[account]
#[derive(InitSpace)]
pub struct UserSubscription {
    pub user: Pubkey,
    pub tier: SubscriptionTier,
    pub started_at: i64,
    pub expires_at: i64,
    pub positions_monitored: u8,
    pub alerts_enabled: bool,
    pub auto_protect_enabled: bool,
    pub bump: u8,
}
