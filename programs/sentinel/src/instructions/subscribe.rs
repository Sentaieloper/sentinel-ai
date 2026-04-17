use anchor_lang::prelude::*;
use anchor_lang::system_program;
use crate::state::*;
use crate::constants::*;
use crate::errors::SentinelError;

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
    /// CHECK: address is verified against config.treasury.
    #[account(
        mut,
        address = config.treasury @ SentinelError::Unauthorized,
    )]
    pub treasury: UncheckedAccount<'info>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<Subscribe>, tier: SubscriptionTier) -> Result<()> {
    let clock = Clock::get()?;

    // Pro tier pays subscription_price_monthly to treasury. Free is free.
    if tier == SubscriptionTier::Pro {
        let price = ctx.accounts.config.subscription_price_monthly;
        require!(price > 0, SentinelError::InvalidPrice);
        let cpi = system_program::Transfer {
            from: ctx.accounts.user.to_account_info(),
            to: ctx.accounts.treasury.to_account_info(),
        };
        let cpi_ctx = CpiContext::new(
            ctx.accounts.system_program.to_account_info(),
            cpi,
        );
        system_program::transfer(cpi_ctx, price)?;
    }

    let sub = &mut ctx.accounts.subscription;
    sub.user = ctx.accounts.user.key();
    sub.tier = tier;
    sub.started_at = clock.unix_timestamp;
    sub.expires_at = clock.unix_timestamp
        .checked_add(30_i64.checked_mul(86_400).ok_or(SentinelError::MathOverflow)?)
        .ok_or(SentinelError::MathOverflow)?;
    sub.positions_monitored = 0;
    sub.alerts_enabled = true;
    sub.auto_protect_enabled = tier == SubscriptionTier::Pro;
    sub.bump = ctx.bumps.subscription;

    ctx.accounts.config.total_users = ctx.accounts.config.total_users
        .checked_add(1)
        .ok_or(SentinelError::MathOverflow)?;
    Ok(())
}
