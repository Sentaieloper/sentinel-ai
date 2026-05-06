use anchor_lang::prelude::*;
use anchor_lang::system_program;
use crate::state::*;
use crate::errors::SentinelError;
use crate::constants::*;

#[derive(Accounts)]
#[instruction(nonce: u64)]
pub struct OpenLeveragedPosition<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + LeveragedPosition::INIT_SPACE,
        seeds = [LEVERAGED_SEED, authority.key().as_ref(), &nonce.to_le_bytes()],
        bump,
    )]
    pub position: Account<'info, LeveragedPosition>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

pub fn handler(
    ctx: Context<OpenLeveragedPosition>,
    nonce: u64,
    asset: SupportedAsset,
    direction: PositionDirection,
    collateral_lamports: u64,
    leverage_bps: u16,
    entry_price_micro: u64,
) -> Result<()> {
    require!(
        collateral_lamports >= MIN_COLLATERAL_LAMPORTS,
        SentinelError::InsufficientCollateral
    );
    require!(
        leverage_bps >= MIN_LEVERAGE_BPS && leverage_bps <= MAX_LEVERAGE_BPS,
        SentinelError::InvalidLeverage
    );
    require!(entry_price_micro > 0, SentinelError::InvalidPrice);

    let cpi_accounts = system_program::Transfer {
        from: ctx.accounts.authority.to_account_info(),
        to: ctx.accounts.position.to_account_info(),
    };
    let cpi_ctx = CpiContext::new(
        ctx.accounts.system_program.to_account_info(),
        cpi_accounts,
    );
    system_program::transfer(cpi_ctx, collateral_lamports)?;

    let pos = &mut ctx.accounts.position;
    let clock = Clock::get()?;
    pos.authority = ctx.accounts.authority.key();
    pos.nonce = nonce;
    pos.asset = asset;
    pos.direction = direction;
    pos.collateral_lamports = collateral_lamports;
    pos.leverage_bps = leverage_bps;
    pos.entry_price_micro = entry_price_micro;
    pos.opened_at = clock.unix_timestamp;
    pos.bump = ctx.bumps.position;

    Ok(())
}
