use anchor_lang::prelude::*;

#[account]
#[derive(InitSpace)]
pub struct SentinelConfig {
    pub authority: Pubkey,
    pub treasury: Pubkey,
    pub subscription_price_monthly: u64,
    pub total_users: u64,
    pub bump: u8,
}
