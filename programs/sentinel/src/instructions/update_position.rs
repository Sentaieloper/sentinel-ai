use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::SentinelError;
use crate::constants::*;

#[derive(Accounts)]
pub struct UpdatePosition<'info> {
    #[account(
        seeds = [CONFIG_SEED],
        bump = config.bump,
        constraint = config.authority == crank.key() @ SentinelError::Unauthorized,
    )]
    pub config: Account<'info, SentinelConfig>,
    #[account(mut)]
    pub position: Account<'info, MonitoredPosition>,
    pub crank: Signer<'info>,
}

pub fn handler(
    ctx: Context<UpdatePosition>,
    health_factor: u16,
    collateral_value: u64,
    debt_value: u64,
) -> Result<()> {
    let clock = Clock::get()?;
    let pos = &mut ctx.accounts.position;

    pos.health_factor = health_factor;
    pos.collateral_value = collateral_value;
    pos.debt_value = debt_value;
    pos.last_checked = clock.unix_timestamp;

    // SECURITY: Evaluate risk level based on health factor thresholds
    pos.risk_level = if health_factor >= WARNING_THRESHOLD {
        RiskLevel::Safe
    } else if health_factor >= DANGER_THRESHOLD {
        RiskLevel::Warning
    } else if health_factor >= CRITICAL_THRESHOLD {
        RiskLevel::Danger
    } else {
        RiskLevel::Critical
    };

    Ok(())
}
