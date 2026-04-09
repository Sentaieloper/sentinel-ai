use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::SentinelError;
use crate::constants::*;

#[derive(Accounts)]
pub struct AddPosition<'info> {
    #[account(
        mut,
        seeds = [SUBSCRIPTION_SEED, user.key().as_ref()],
        bump = subscription.bump,
    )]
    pub subscription: Account<'info, UserSubscription>,
    #[account(
        init,
        payer = user,
        space = 8 + MonitoredPosition::INIT_SPACE,
        seeds = [POSITION_SEED, user.key().as_ref(), position_address.key().as_ref()],
        bump,
    )]
    pub position: Account<'info, MonitoredPosition>,
    /// CHECK: The external DeFi position account to monitor
    pub position_address: UncheckedAccount<'info>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<AddPosition>, protocol: SupportedProtocol) -> Result<()> {
    let sub = &ctx.accounts.subscription;
    let max = match sub.tier {
        SubscriptionTier::Free => FREE_TIER_MAX_POSITIONS,
        SubscriptionTier::Pro => PRO_TIER_MAX_POSITIONS,
    };
    require!(sub.positions_monitored < max, SentinelError::PositionLimitReached);

    let clock = Clock::get()?;
    let pos = &mut ctx.accounts.position;
    pos.user = ctx.accounts.user.key();
    pos.protocol = protocol;
    pos.position_address = ctx.accounts.position_address.key();
    pos.health_factor = HEALTH_FACTOR_DECIMALS * 2; // default: 2.0 (safe)
    pos.liquidation_threshold = DANGER_THRESHOLD;
    pos.collateral_value = 0;
    pos.debt_value = 0;
    pos.last_checked = clock.unix_timestamp;
    pos.risk_level = RiskLevel::Safe;
    pos.auto_protect = false;
    pos.alert_sent = false;
    pos.bump = ctx.bumps.position;

    ctx.accounts.subscription.positions_monitored += 1;
    Ok(())
}
