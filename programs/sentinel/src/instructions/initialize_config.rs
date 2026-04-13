use anchor_lang::prelude::*;
use crate::state::SentinelConfig;
use crate::constants::CONFIG_SEED;

#[derive(Accounts)]
pub struct InitializeConfig<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + SentinelConfig::INIT_SPACE,
        seeds = [CONFIG_SEED],
        bump,
    )]
    pub config: Account<'info, SentinelConfig>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<InitializeConfig>, subscription_price: u64) -> Result<()> {
    let config = &mut ctx.accounts.config;
    config.authority = ctx.accounts.authority.key();
    config.treasury = ctx.accounts.authority.key();
    config.subscription_price_monthly = subscription_price;
    config.total_users = 0;
    config.bump = ctx.bumps.config;
    Ok(())
}
