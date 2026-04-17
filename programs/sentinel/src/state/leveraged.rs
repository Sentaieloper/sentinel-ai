use anchor_lang::prelude::*;

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum SupportedAsset {
    Sol,
    Btc,
    Eth,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum PositionDirection {
    Long,
    Short,
}

#[account]
#[derive(InitSpace)]
pub struct LeveragedPosition {
    pub authority: Pubkey,
    pub nonce: u64,
    pub asset: SupportedAsset,
    pub direction: PositionDirection,
    pub collateral_lamports: u64,
    pub leverage_bps: u16,
    pub entry_price_micro: u64,
    pub opened_at: i64,
    pub bump: u8,
}
