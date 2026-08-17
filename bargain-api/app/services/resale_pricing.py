"""Resale Pricing Assistant — repricing suggestions for arbitrage flips.

Marketplace repricers (Informed Repricer, etc.) exist to help sellers with an
established catalog defend the Buy Box on listings they already have. This is
the same idea applied to arbitrage resale: for an item a user bought to flip,
periodically compare their asking price against the current market price and
suggest an adjustment.

Strategy (deliberately simple — this isn't trying to replicate a full
enterprise repricer):
  - If the market price has dropped below our asking price, suggest dropping
    to just under the market price (to stay competitive) but never below
    ``min_price`` (defaults to buy_price, i.e. never suggest selling at a
    loss unless the user explicitly sets a lower floor).
  - If the market price has risen above our asking price, suggest raising
    price to just under the market price — Informed Repricer's "raise the
    price, not lower it" idea — instead of leaving profit on the table.
  - If the market price roughly matches our price, no change is suggested.

Market price currently comes from ``get_ebay_market_price`` (sold-comp
median), which is the same function the core arbitrage engine already uses.
It is not a live "lowest active listing" feed — see that function's own
docstring for why (eBay scraping from cloud IPs has the same reliability
caveats as Amazon/Walmart). Treat suggestions as directional, not exact.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
from typing import Optional
import logging

from app.services.ebay_scraper import get_ebay_market_price

logger = logging.getLogger(__name__)

# Minimum price step to bother suggesting a change (avoid noisy penny-chasing)
MIN_CHANGE_THRESHOLD = Decimal("0.50")
# Default cushion below/above the competitor price when repricing
UNDERCUT_STEP = Decimal("0.01")


@dataclass
class RepriceResult:
    competitor_price: Optional[Decimal]
    suggested_price: Optional[Decimal]
    reason: str
    checked_at: datetime


def _round_cents(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def compute_suggested_price(
    our_price: Decimal,
    competitor_price: Optional[Decimal],
    min_price: Optional[Decimal],
) -> tuple[Optional[Decimal], str]:
    """Pure pricing logic, split out from the network call for easy testing."""
    if competitor_price is None:
        return None, "No competitor pricing data available"

    floor = min_price if min_price is not None else Decimal("0")

    diff = competitor_price - our_price

    if abs(diff) < MIN_CHANGE_THRESHOLD:
        return None, f"Already competitive (within ${MIN_CHANGE_THRESHOLD} of market price)"

    if diff < 0:
        # Market price dropped below ours — undercut it slightly to stay competitive,
        # but never suggest going below the floor.
        candidate = _round_cents(competitor_price - UNDERCUT_STEP)
        if candidate < floor:
            if our_price <= floor:
                return None, "Market price dropped below your floor price — no safe change to suggest"
            return _round_cents(floor), "Market price dropped — lowering to your floor to stay competitive"
        return candidate, f"Market price dropped to ${competitor_price} — lower to stay competitive"

    # Market price rose above ours — raise to capture the extra margin instead
    # of leaving money on the table (mirrors "raise the price, not lower it").
    candidate = _round_cents(competitor_price - UNDERCUT_STEP)
    return candidate, f"Market price rose to ${competitor_price} — raise price to capture more profit"


async def refresh_resale_listing_price(listing) -> RepriceResult:
    """Check current market price for a ResaleListing and compute a suggestion.

    Does not persist changes — caller is responsible for saving the updated
    fields to the listing and committing the session.
    """
    query = listing.search_query or listing.title
    competitor_price = await get_ebay_market_price(query, limit=10)

    our_price = Decimal(str(listing.our_price))
    min_price = Decimal(str(listing.min_price)) if listing.min_price is not None else (
        Decimal(str(listing.buy_price)) if listing.buy_price is not None else None
    )

    suggested, reason = compute_suggested_price(our_price, competitor_price, min_price)

    return RepriceResult(
        competitor_price=competitor_price,
        suggested_price=suggested,
        reason=reason,
        checked_at=datetime.utcnow(),
    )
