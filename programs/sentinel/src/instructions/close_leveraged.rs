use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::SentinelError;
use crate::constants::*;

#[derive(Accounts)]
pub struct CloseLeveragedPosition<'info> {
    #[account(
        mut,
        close = authority,
        seeds = [LEVERAGED_SEED, authority.key().as_ref(), &position.nonce.to_le_bytes()],
        bump = position.bump,
        has_one = authority @ SentinelError::Unauthorized,
    )]
    pub position: Account<'info, LeveragedPosition>,
    #[account(mut)]
    pub authority: Signer<'info>,
}

pub fn handler(
    ctx: Context<CloseLeveragedPosition>,
    exit_price_micro: u64,
) -> Result<()> {
    require!(exit_price_micro > 0, SentinelError::InvalidPrice);
    // Settlement is simulated: `close = authority` returns full collateral
    // plus rent-exempt lamports to the signer. PnL is computed and displayed
    // off-chain from stored entry price vs the supplied exit price.
    msg!(
        "close: nonce={} entry={} exit={}",
        ctx.accounts.position.nonce,
        ctx.accounts.position.entry_price_micro,
        exit_price_micro
    );
    Ok(())
}
