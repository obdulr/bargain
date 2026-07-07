"""
Deal Criteria Engine — Phase 1

Evaluates deals against multiple criteria tiers:
- Glitch: 70%+ below historical average (immediate alert)
- Clearance: 50-70% below historical average (standard alert)
- Arbitrage: 30%+ price gap between platforms (arbitrage alert)
- Watch: 20-30% below historical average (log only)

Also applies anti-noise filters:
- Minimum price: $10
- Maximum price: $500
- Minimum 3 historical data points before alerting
- Duplicate detection: 24h cooldown per ASIN/UPC
- Price drop velocity: Flag if >50% drop in <1hr
"""

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


class DealTier(str, Enum):
    GLITCH = "glitch"
    CLEARANCE = "clearance"
    ARBITRAGE = "arbitrage"
    WATCH = "watch"
    REJECTED = "rejected"


class DealStatus(str, Enum):
    PENDING = "pending"
    ALERTED = "alerted"
    EXPIRED = "expired"
    REJECTED = "rejected"


@dataclass
class DealCriteria:
    """Configurable criteria for deal evaluation."""
    # Discrepancy thresholds (percentage as decimal, e.g. 0.50 = 50%)
    glitch_threshold: Decimal = Decimal("0.70")
    clearance_threshold: Decimal = Decimal("0.50")
    arbitrage_threshold: Decimal = Decimal("0.30")
    watch_threshold: Decimal = Decimal("0.20")

    # Price bounds
    min_price: Decimal = Decimal("10.00")
    max_price: Decimal = Decimal("500.00")

    # Profitability
    min_net_profit: Decimal = Decimal("5.00")
    min_roi: Decimal = Decimal("0.25")  # 25% ROI minimum

    # Data requirements
    min_history_points: int = 3

    # Cooldown
    duplicate_cooldown_hours: int = 24

    # Velocity detection
    velocity_threshold: Decimal = Decimal("0.50")  # 50% drop in 1hr = glitch
    velocity_window_minutes: int = 60


# Default singleton
default_criteria = DealCriteria()


@dataclass
class PriceHistory:
    """Historical price data for a product."""
    prices: list[tuple[datetime, Decimal]] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.prices)

    @property
    def average(self) -> Optional[Decimal]:
        if not self.prices:
            return None
        total = sum(p for _, p in self.prices)
        return (total / len(self.prices)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def median(self) -> Optional[Decimal]:
        if not self.prices:
            return None
        sorted_prices = sorted(p for _, p in self.prices)
        n = len(sorted_prices)
        if n % 2 == 0:
            mid = (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / 2
        else:
            mid = sorted_prices[n // 2]
        return mid.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def lowest(self) -> Optional[Decimal]:
        if not self.prices:
            return None
        return min(p for _, p in self.prices)

    @property
    def highest(self) -> Optional[Decimal]:
        if not self.prices:
            return None
        return max(p for _, p in self.prices)

    def price_drop_velocity(self, current: Decimal, window_minutes: int = 60) -> Optional[Decimal]:
        """Calculate the percentage drop in the last N minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent = [(ts, p) for ts, p in self.prices if ts >= cutoff]
        if not recent:
            return None
        oldest_in_window = min(p for _, p in recent)
        if oldest_in_window == 0:
            return None
        drop = (oldest_in_window - current) / oldest_in_window
        return drop.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


@dataclass
class DealEvaluation:
    """Result of evaluating a deal against criteria."""
    tier: DealTier
    status: DealStatus
    discrepancy: Optional[Decimal] = None
    velocity_drop: Optional[Decimal] = None
    reason: str = ""
    should_alert: bool = False


def evaluate_discrepancy(
    current_price: Decimal,
    historical: PriceHistory,
    criteria: DealCriteria = default_criteria,
) -> DealEvaluation:
    """Evaluate a price against historical data for discrepancy-based deals.

    This handles glitch, clearance, and watch tiers.
    """
    # Anti-noise: minimum history
    if historical.count < criteria.min_history_points:
        return DealEvaluation(
            tier=DealTier.REJECTED,
            status=DealStatus.REJECTED,
            reason=f"Insufficient history ({historical.count}/{criteria.min_history_points} points)",
        )

    # Anti-noise: price bounds
    if current_price < criteria.min_price:
        return DealEvaluation(
            tier=DealTier.REJECTED,
            status=DealStatus.REJECTED,
            reason=f"Price below minimum (${current_price} < ${criteria.min_price})",
        )
    if current_price > criteria.max_price:
        return DealEvaluation(
            tier=DealTier.REJECTED,
            status=DealStatus.REJECTED,
            reason=f"Price above maximum (${current_price} > ${criteria.max_price})",
        )

    avg = historical.average
    if avg is None or avg == 0:
        return DealEvaluation(
            tier=DealTier.REJECTED,
            status=DealStatus.REJECTED,
            reason="No historical average available",
        )

    discrepancy = (avg - current_price) / avg

    # Check for velocity-based glitch (rapid price drop)
    velocity_drop = historical.price_drop_velocity(current_price, criteria.velocity_window_minutes)
    if velocity_drop and velocity_drop >= criteria.velocity_threshold:
        return DealEvaluation(
            tier=DealTier.GLITCH,
            status=DealStatus.PENDING,
            discrepancy=discrepancy,
            velocity_drop=velocity_drop,
            reason=f"Velocity glitch: {velocity_drop*100:.1f}% drop in {criteria.velocity_window_minutes}min",
            should_alert=True,
        )

    # Standard discrepancy tiers
    if discrepancy >= criteria.glitch_threshold:
        return DealEvaluation(
            tier=DealTier.GLITCH,
            status=DealStatus.PENDING,
            discrepancy=discrepancy,
            velocity_drop=velocity_drop,
            reason=f"Glitch: {discrepancy*100:.1f}% below average",
            should_alert=True,
        )
    elif discrepancy >= criteria.clearance_threshold:
        return DealEvaluation(
            tier=DealTier.CLEARANCE,
            status=DealStatus.PENDING,
            discrepancy=discrepancy,
            velocity_drop=velocity_drop,
            reason=f"Clearance: {discrepancy*100:.1f}% below average",
            should_alert=True,
        )
    elif discrepancy >= criteria.watch_threshold:
        return DealEvaluation(
            tier=DealTier.WATCH,
            status=DealStatus.PENDING,
            discrepancy=discrepancy,
            velocity_drop=velocity_drop,
            reason=f"Watch: {discrepancy*100:.1f}% below average",
            should_alert=False,  # Log only, no alert
        )

    return DealEvaluation(
        tier=DealTier.REJECTED,
        status=DealStatus.REJECTED,
        discrepancy=discrepancy,
        reason=f"Discrepancy too low ({discrepancy*100:.1f}% < {criteria.watch_threshold*100:.0f}%)",
    )
