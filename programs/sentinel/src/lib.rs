use anchor_lang::prelude::*;

mod state;
mod errors;
mod constants;
mod instructions;

use instructions::*;

declare_id!("5QiE51bSE3yqJFmRhj1CHt2NwaJpC2iodsaLDrZJDheE");

/// Subscription and monitoring program for DeFi positions.

#[program]
pub mod sentinel {
    use super::*;

    pub fn initialize_config(ctx: Context<InitializeConfig>, subscription_price: u64) -> Result<()> {
        instructions::initialize_config::handler(ctx, subscription_price)
    }

    pub fn subscribe(ctx: Context<Subscribe>, tier: state::SubscriptionTier) -> Result<()> {
        instructions::subscribe::handler(ctx, tier)
    }

    pub fn add_position(ctx: Context<AddPosition>, protocol: state::SupportedProtocol) -> Result<()> {
        instructions::add_position::handler(ctx, protocol)
    }

    pub fn update_position(
        ctx: Context<UpdatePosition>,
        health_factor: u16,
        collateral_value: u64,
        debt_value: u64,
    ) -> Result<()> {
        instructions::update_position::handler(ctx, health_factor, collateral_value, debt_value)
    }

    pub fn create_alert(
        ctx: Context<CreateAlert>,
        alert_id: u64,
        alert_type: state::AlertType,
        predicted_liquidation_time: Option<i64>,
    ) -> Result<()> {
        instructions::create_alert::handler(ctx, alert_id, alert_type, predicted_liquidation_time)
    }
}
