use anchor_lang::prelude::*;

#[error_code]
pub enum SentinelError {
    #[msg("SECURITY: Unauthorized access attempt")]
    Unauthorized,
    #[msg("SECURITY: Subscription expired")]
    SubscriptionExpired,
    #[msg("Pro subscription required for this feature")]
    ProRequired,
    #[msg("Position limit reached for current tier")]
    PositionLimitReached,
    #[msg("Unsupported protocol")]
    UnsupportedProtocol,
    #[msg("Position already registered")]
    PositionAlreadyExists,
    #[msg("Math overflow in calculation")]
    MathOverflow,
}
