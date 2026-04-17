use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::SentinelError;
use crate::constants::*;

#[derive(Accounts)]
#[instruction(alert_id: u64)]
pub struct CreateAlert<'info> {
    #[account(
        seeds = [CONFIG_SEED],
        bump = config.bump,
        constraint = config.authority == crank.key() @ SentinelError::Unauthorized,
    )]
    pub config: Account<'info, SentinelConfig>,
    #[account(
        init,
        payer = crank,
        space = 8 + AlertLog::INIT_SPACE,
        seeds = [ALERT_SEED, user.key().as_ref(), &alert_id.to_le_bytes()],
        bump,
    )]
    pub alert: Account<'info, AlertLog>,
    /// CHECK: User who owns the position, validated via position.user constraint
    #[account(constraint = position.user == user.key() @ SentinelError::Unauthorized)]
    pub user: UncheckedAccount<'info>,
    #[account(
        seeds = [POSITION_SEED, position.user.as_ref(), position.position_address.as_ref()],
        bump = position.bump,
    )]
    pub position: Account<'info, MonitoredPosition>,
    #[account(mut)]
    pub crank: Signer<'info>,
    pub system_program: Program<'info, System>,
}

pub fn handler(
    ctx: Context<CreateAlert>,
    _alert_id: u64,
    alert_type: AlertType,
    predicted_liquidation_time: Option<i64>,
) -> Result<()> {
    let clock = Clock::get()?;
    let alert = &mut ctx.accounts.alert;
    alert.user = ctx.accounts.user.key();
    alert.position = ctx.accounts.position.key();
    alert.alert_type = alert_type;
    alert.health_factor_at_alert = ctx.accounts.position.health_factor;
    alert.predicted_liquidation_time = predicted_liquidation_time;
    alert.action_taken = None;
    alert.created_at = clock.unix_timestamp;
    alert.bump = ctx.bumps.alert;
    Ok(())
}
