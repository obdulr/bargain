"""Price prediction service using historical price data.

Predicts whether a deal price is likely to drop further (wait) or if
it's at/near the lowest point (buy now). Uses a simple linear regression
on recent price history plus volatility analysis.

This is a PRO/ENTERPRISE feature — free users get basic predictions,
paid users get detailed analysis.
"""
from datetime import datetime, timedelta
from typing import Optional
import logging
import statistics

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False
    logger.info("numpy not installed — price predictor using stdlib fallback")


def volatility_score(stdev: float, mean: float) -> float:
    """Normalize volatility to 0-20 scale."""
    if mean <= 0:
        return 20
    cv = stdev / mean  # coefficient of variation
    return min(20, cv * 100)


class PricePredictor:
    """Predicts price movement based on historical data."""

    def __init__(self):
        self.min_data_points = 5

    def predict_price_trend(self, price_history: list[dict]) -> dict:
        """Analyze price history and predict near-term trend.

        Args:
            price_history: List of {"timestamp": ..., "price": float} sorted
                oldest to newest.

        Returns:
            {
                "recommendation": "buy_now" | "wait" | "monitor",
                "confidence": 0-100,
                "predicted_low": float,  # predicted lowest price in next 7 days
                "current_vs_predicted": float,  # % difference
                "trend": "decreasing" | "stable" | "increasing",
                "volatility": float,  # price volatility score
                "days_to_lowest": int,  # estimated days until lowest price
            }
        """
        if len(price_history) < self.min_data_points:
            return {
                "recommendation": "monitor",
                "confidence": 0,
                "predicted_low": None,
                "current_vs_predicted": 0,
                "trend": "stable",
                "volatility": 0,
                "days_to_lowest": 0,
                "message": "Insufficient price history for prediction",
            }

        prices = [float(p["price"]) for p in price_history]
        current_price = prices[-1]

        if _HAS_NUMPY:
            arr = np.array(prices)
            x = np.arange(len(arr))
            coeffs = np.polyfit(x, arr, 1)
            slope = float(coeffs[0])
            price_changes = np.diff(arr)
            volatility = float(np.std(price_changes)) if len(price_changes) > 1 else 0
            future_x = np.arange(len(arr), len(arr) + 7)
            predicted = np.polyval(coeffs, future_x)
            predicted_low = float(np.min(predicted))
        else:
            # Stdlib fallback: simple linear regression
            n = len(prices)
            x_mean = sum(range(n)) / n
            y_mean = sum(prices) / n
            num = sum((i - x_mean) * (p - y_mean) for i, p in enumerate(prices))
            den = sum((i - x_mean) ** 2 for i in range(n))
            slope = num / den if den != 0 else 0
            intercept = y_mean - slope * x_mean
            price_changes = [prices[i+1] - prices[i] for i in range(n-1)]
            volatility = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
            predicted = [slope * (n + i) + intercept for i in range(7)]
            predicted_low = min(predicted)

        # Trend analysis
        if slope < -0.5 * volatility:
            trend = "decreasing"
        elif slope > 0.5 * volatility:
            trend = "increasing"
        else:
            trend = "stable"

        # Recommendation
        current_vs_predicted = (
            ((current_price - predicted_low) / current_price * 100)
            if current_price > 0
            else 0
        )

        if trend == "decreasing" and current_vs_predicted > 5:
            recommendation = "wait"
            confidence = min(80, int(abs(current_vs_predicted) * 3))
        elif trend == "stable" or current_vs_predicted < 2:
            recommendation = "buy_now"
            confidence = min(90, int(100 - volatility / max(current_price, 1) * 1000))
        else:
            recommendation = "monitor"
            confidence = 50

        # Estimate days to lowest
        if trend == "decreasing":
            if _HAS_NUMPY:
                days_to_lowest = int(np.argmin(predicted)) + 1
            else:
                days_to_lowest = predicted.index(min(predicted)) + 1
        else:
            days_to_lowest = 0

        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "predicted_low": round(predicted_low, 2),
            "current_vs_predicted": round(current_vs_predicted, 2),
            "trend": trend,
            "volatility": round(volatility, 2),
            "days_to_lowest": days_to_lowest,
        }

    def score_deal_quality(
        self,
        price_history: list[dict],
        current_price: float,
        historical_avg: float,
    ) -> dict:
        """Score a deal's quality using ML features.

        Returns a 0-100 score where higher = better deal.
        """
        if len(price_history) < self.min_data_points:
            # Fall back to simple comparison
            if historical_avg > 0:
                discount = (historical_avg - current_price) / historical_avg * 100
                return {"score": min(100, int(discount * 2)), "method": "simple_discount"}
            return {"score": 50, "method": "insufficient_data"}

        prices = [float(p["price"]) for p in price_history]

        if _HAS_NUMPY:
            arr = np.array(prices)
            percentile_rank = float(np.sum(arr <= current_price) / len(arr) * 100)
            price_stdev = float(np.std(arr))
            price_mean = float(np.mean(arr))
        else:
            percentile_rank = sum(1 for p in prices if p <= current_price) / len(prices) * 100
            price_stdev = statistics.stdev(prices) if len(prices) > 1 else 0
            price_mean = statistics.mean(prices)

        z_score = (current_price - price_mean) / max(price_stdev, 0.01)

        # Recent trend
        recent_prices = prices[-5:] if len(prices) >= 5 else prices
        recent_trend = (recent_prices[-1] - recent_prices[0]) / max(recent_prices[0], 0.01) * 100

        # Score: lower percentile rank = better, more negative z-score = better
        score = 0
        score += max(0, 100 - percentile_rank) * 0.4  # 40% weight: how low is current price vs history
        score += max(0, min(50, -z_score * 15)) * 0.3  # 30% weight: z-score
        score += max(0, min(30, -recent_trend * 2)) * 0.2  # 20% weight: recent downward trend
        score += max(0, 20 - volatility_score(price_stdev, price_mean)) * 0.1  # 10% weight: stability

        return {
            "score": min(100, max(0, int(score))),
            "method": "ml_features",
            "percentile_rank": round(percentile_rank, 1),
            "z_score": round(z_score, 2),
            "recent_trend_pct": round(recent_trend, 2),
        }


# Singleton
price_predictor = PricePredictor()
