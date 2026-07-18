"""Deal Scoring Service.

Calculates a composite quality score for arbitrage deals (0-100+ scale).
Higher score = better deal = more likely to convert.

The score is used to prioritize which deals get posted to social media
and which appear first in the deals feed, ensuring the best deals
(high discount, popular product, good price point) surface ahead of
merely "new" deals.

Scoring components:
  1. Discount percentage   (0-50 points) — bigger discount = better deal
  2. BSR (Best Sellers Rank) (0-30 points) — lower BSR = more popular
  3. Deal tier bonus       (0-15 points) — glitch > clearance > arbitrage
  4. Price point bonus     (0-5 points)  — impulse-buy range scores higher
  5. Platform bonus        (0-5 points)  — Amazon converts best
"""
import logging

logger = logging.getLogger(__name__)


def calculate_deal_score(deal) -> float:
    """Calculate a composite quality score for a deal (0-100+ scale).
    Higher score = better deal = more likely to convert.
    """
    score = 0.0

    # 1. Discount percentage (0-50 points)
    # Calculate discount from buy_price and sell_price (or historical_avg)
    original_price = float(deal.sell_price or deal.historical_avg or 0)
    current_price = float(deal.buy_price or 0)
    if original_price > 0 and current_price > 0:
        discount_pct = ((original_price - current_price) / original_price) * 100
        # 50% discount = 50 points, 75%+ = capped at 50
        score += min(50, discount_pct)

    # 2. BSR (Best Sellers Rank) — lower BSR = more popular (0-30 points)
    if deal.bsr and deal.bsr > 0:
        if deal.bsr <= 1000:
            score += 30  # Top 1000 = very popular
        elif deal.bsr <= 10000:
            score += 20  # Top 10K = popular
        elif deal.bsr <= 50000:
            score += 10  # Top 50K = moderate
        elif deal.bsr <= 100000:
            score += 5   # Top 100K = okay
        # BSR > 100K = 0 points

    # 3. Deal tier bonus (0-15 points)
    tier_bonuses = {"glitch": 15, "clearance": 10, "arbitrage": 5, "watch": 0}
    score += tier_bonuses.get(deal.deal_tier, 0)

    # 4. Price point bonus — sweet spot for impulse buys (0-5 points)
    if current_price > 0:
        if current_price <= 25:
            score += 5  # Impulse buy range
        elif current_price <= 50:
            score += 4  # Easy purchase
        elif current_price <= 100:
            score += 2  # Moderate consideration
        elif current_price <= 200:
            score += 1  # Higher consideration
        # > $200 = 0 points (big purchase, lower conversion)

    # 5. Platform bonus — Amazon converts best (0-5 points)
    platform_bonuses = {"amazon": 5, "walmart": 3, "target": 3, "bestbuy": 2, "ebay": 1}
    score += platform_bonuses.get((deal.buy_platform or "").lower(), 0)

    return round(score, 4)


def update_deal_scores(db, batch_size=100):
    """Update scores for all active deals that haven't been scored yet."""
    from app.db.models import ArbitrageDeal

    deals = db.query(ArbitrageDeal).filter(
        ArbitrageDeal.status == "active",
        ArbitrageDeal.score == 0
    ).limit(batch_size).all()
    for deal in deals:
        deal.score = calculate_deal_score(deal)
    db.commit()
    return len(deals)
