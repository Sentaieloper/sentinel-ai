use anchor_lang::prelude::*;
use crate::state::*;
use crate::constants::*;

#[derive(Accounts)]
pub struct Subscribe<'info> {
    #[account(
        mut,
        seeds = [CONFIG_SEED],
        bump = config.bump,
    )]
    pub config: Account<'info, SentinelConfig>,
    #[account(
        init,
        payer = user,
        space = 8 + UserSubscription::INIT_SPACE,
        seeds = [SUBSCRIPTION_SEED, user.key().as_ref()],
        bump,
    )]
    pub subscription: Account<'info, UserSubscription>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<Subscribe>, tier: SubscriptionTier) -> Result<()> {
    let clock = Clock::get()?;
    let sub = &mut ctx.accounts.subscription;
    sub.user = ctx.accounts.user.key();
    sub.tier = tier;
    sub.started_at = clock.unix_timestamp;
    sub.expires_at = clock.unix_timestamp
        .checked_add(30_i64.checked_mul(86_400).ok_or(crate::errors::SentinelError::MathOverflow)?)
        .ok_or(crate::errors::SentinelError::MathOverflow)?;
    sub.positions_monitored = 0;
    sub.alerts_enabled = true;
    sub.auto_protect_enabled = tier == SubscriptionTier::Pro;
    sub.bump = ctx.bumps.subscription;

    ctx.accounts.config.total_users = ctx.accounts.config.total_users
        .checked_add(1)
        .ok_or(crate::errors::SentinelError::MathOverflow)?;
    Ok(())
}
