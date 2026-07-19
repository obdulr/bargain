"""Critical-path tests for the BargainHuntrs API.

Covers:
  1. Auth flow (register → login → profile, JWT verification)
  2. Deal scoring (high-score vs low-score deals)
  3. Affiliate tag deduplication
  4. UTM parameter injection (no duplication)
  5. Deal tier classification

Database-dependent operations are mocked via the ``db_mock`` / ``client``
fixtures defined in ``conftest.py``.
"""
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from app.routers.auth import create_access_token, create_refresh_token
from app.services.deal_scorer import calculate_deal_score
from app.services.affiliate_service import add_amazon_affiliate
from app.services.utm_service import add_utm_parameters
from app.services.amazon_deals_scraper import _deal_tier_for, AmazonDeal


# ════════════════════════════════════════════════════════════════════════
# 1. AUTH FLOW
# ════════════════════════════════════════════════════════════════════════
class TestAuthFlow:
    """Register → Login → Get profile, verifying JWT tokens throughout."""

    def test_register_returns_jwt_tokens(self, client, db_mock):
        """Registering a new user returns access + refresh JWT tokens."""
        db_mock.first_return = None  # no existing user

        with patch("app.routers.auth.send_welcome_email"):
            resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@test.com",
                    "password": "SecretPass123!",
                    "firstName": "Test",
                    "lastName": "User",
                },
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "accessToken" in data
        assert "refreshToken" in data
        assert data["expiresIn"] > 0
        assert data["user"]["email"] == "newuser@test.com"
        # JWT tokens have three base64 segments separated by dots
        assert data["accessToken"].count(".") == 2
        assert data["refreshToken"].count(".") == 2

    def test_full_auth_flow(self, client, db_mock):
        """Register, then login, then fetch profile with the JWT token."""
        # ── Step 1: Register ────────────────────────────────────────────
        db_mock.first_return = None  # no existing user

        with patch("app.routers.auth.send_welcome_email"):
            resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "flow@test.com",
                    "password": "SecretPass123!",
                    "firstName": "Flow",
                    "lastName": "Tester",
                },
            )
        assert resp.status_code == 200, resp.text
        register_data = resp.json()
        access_token = register_data["accessToken"]

        # Capture the user object created during registration
        registered_user = db_mock.added[0]

        # ── Step 2: Login ───────────────────────────────────────────────
        db_mock.reset()
        db_mock.first_return = registered_user  # simulate finding the user

        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "flow@test.com",
                "password": "SecretPass123!",
            },
        )
        assert resp.status_code == 200, resp.text
        login_data = resp.json()
        assert "accessToken" in login_data
        assert "refreshToken" in login_data
        assert login_data["user"]["email"] == "flow@test.com"

        # ── Step 3: Get profile ─────────────────────────────────────────
        db_mock.reset()
        db_mock.first_return = registered_user  # simulate finding the user

        resp = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200, resp.text
        profile = resp.json()
        assert profile["success"] is True
        assert profile["email"] == "flow@test.com"
        assert profile["firstName"] == "Flow"

    def test_login_wrong_password(self, client, db_mock):
        """Login with incorrect credentials returns 401."""
        # First register to get a user with a known password hash
        db_mock.first_return = None
        with patch("app.routers.auth.send_welcome_email"):
            client.post(
                "/api/v1/auth/register",
                json={"email": "wrongpw@test.com", "password": "SecretPass123!"},
            )
        registered_user = db_mock.added[0]

        # Attempt login with wrong password
        db_mock.reset()
        db_mock.first_return = registered_user

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@test.com", "password": "WrongPassword!"},
        )
        assert resp.status_code == 401

    def test_profile_without_token(self, client, db_mock):
        """Fetching profile without a JWT token returns 401."""
        resp = client.get("/api/v1/auth/profile")
        assert resp.status_code == 401

    def test_jwt_token_is_valid(self, client, db_mock):
        """The JWT token returned by register can be decoded and contains sub."""
        from jose import jwt
        from app.core.config import settings

        db_mock.first_return = None
        with patch("app.routers.auth.send_welcome_email"):
            resp = client.post(
                "/api/v1/auth/register",
                json={"email": "jwt@test.com", "password": "SecretPass123!"},
            )
        token = resp.json()["accessToken"]

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "sub" in payload
        assert "exp" in payload

    def test_refresh_token_flow(self, client, db_mock):
        """A refresh token can be exchanged for a new access token."""
        db_mock.first_return = None
        with patch("app.routers.auth.send_welcome_email"):
            resp = client.post(
                "/api/v1/auth/register",
                json={"email": "refresh@test.com", "password": "SecretPass123!"},
            )
        data = resp.json()
        refresh_token = data["refreshToken"]
        registered_user = db_mock.added[0]
        registered_user.refresh_token = refresh_token

        db_mock.reset()
        db_mock.first_return = registered_user

        resp = client.post(
            "/api/v1/auth/refresh",
            json={"token": refresh_token},
        )
        assert resp.status_code == 200, resp.text
        assert "accessToken" in resp.json()


# ════════════════════════════════════════════════════════════════════════
# 2. DEAL SCORING
# ════════════════════════════════════════════════════════════════════════
class TestDealScoring:
    """Verify calculate_deal_score produces sensible high/low scores."""

    def test_high_score_deal(self):
        """A deal with high discount, low BSR, Amazon platform scores >= 50."""
        deal = SimpleNamespace(
            sell_price=100.0,
            historical_avg=100.0,
            buy_price=25.0,       # 75% discount → 50 pts (capped)
            bsr=500,              # top 1000 → 30 pts
            deal_tier="glitch",   # 15 pts
            buy_platform="amazon",  # 5 pts
        )
        score = calculate_deal_score(deal)
        # 50 (discount) + 30 (bsr) + 15 (tier) + 5 (price ≤$25) + 5 (amazon) = 105
        assert score >= 50, f"Expected high score, got {score}"

    def test_low_score_deal(self):
        """A deal with no discount, high BSR, weak platform scores < 15."""
        deal = SimpleNamespace(
            sell_price=100.0,
            historical_avg=100.0,
            buy_price=100.0,      # 0% discount → 0 pts
            bsr=200000,           # > 100K → 0 pts
            deal_tier="watch",    # 0 pts
            buy_platform="ebay",  # 1 pt
        )
        score = calculate_deal_score(deal)
        # 0 + 0 + 0 + 2 (price ≤$100) + 1 (ebay) = 3
        assert score < 15, f"Expected low score, got {score}"

    def test_score_is_numeric(self):
        """Score is returned as a numeric type and rounded to 4 decimals."""
        deal = SimpleNamespace(
            sell_price=50.0,
            historical_avg=50.0,
            buy_price=40.0,
            bsr=5000,
            deal_tier="arbitrage",
            buy_platform="walmart",
        )
        score = calculate_deal_score(deal)
        assert isinstance(score, (int, float))
        # Should be rounded to at most 4 decimal places
        assert round(score, 4) == score


# ════════════════════════════════════════════════════════════════════════
# 3. AFFILIATE TAG DEDUPLICATION
# ════════════════════════════════════════════════════════════════════════
class TestAffiliateDedup:
    """Verify affiliate tags are not duplicated on repeated calls."""

    def test_tag_added_once(self):
        """Calling add_amazon_affiliate twice only adds the tag once."""
        url = "https://www.amazon.com/dp/B08N5WRWNW"
        tagged = add_amazon_affiliate(url)
        assert "tag=bargainhuntrs-20" in tagged

        double_tagged = add_amazon_affiliate(tagged)
        assert double_tagged.count("tag=bargainhuntrs-20") == 1
        assert double_tagged == tagged  # idempotent

    def test_tag_not_added_to_already_tagged_url(self):
        """A URL that already has a tag is returned unchanged."""
        url = "https://www.amazon.com/dp/B08N5WRWNW?tag=other-tag-20"
        result = add_amazon_affiliate(url)
        assert result == url  # no double-tagging

    def test_preserves_existing_query_params(self):
        """Existing query parameters are preserved when the tag is added."""
        url = "https://www.amazon.com/dp/B08N5WRWNW?ref=nosim"
        tagged = add_amazon_affiliate(url)
        assert "ref=nosim" in tagged
        assert "tag=bargainhuntrs-20" in tagged
        assert tagged.count("?") == 1  # only one question mark


# ════════════════════════════════════════════════════════════════════════
# 4. UTM PARAMETERS
# ════════════════════════════════════════════════════════════════════════
class TestUtmParameters:
    """Verify UTM parameters are added and not duplicated."""

    def test_utm_params_added(self):
        """Calling add_utm_parameters on a plain URL adds all three params."""
        url = "https://example.com/page"
        result = add_utm_parameters(url, "newsletter", "email", "summer2024")

        assert "utm_source=newsletter" in result
        assert "utm_medium=email" in result
        assert "utm_campaign=summer2024" in result

    def test_utm_params_not_duplicated(self):
        """Calling add_utm_parameters again on the result doesn't duplicate values."""
        url = "https://example.com/page"
        result = add_utm_parameters(url, "newsletter", "email", "summer2024")
        result2 = add_utm_parameters(result, "newsletter", "email", "summer2024")

        assert result2.count("utm_source=newsletter") == 1
        assert result2.count("utm_medium=email") == 1
        assert result2.count("utm_campaign=summer2024") == 1

    def test_utm_campaign_always_overridden(self):
        """utm_campaign is always set to the supplied value (overridden)."""
        url = "https://example.com/page?utm_campaign=old_campaign"
        result = add_utm_parameters(url, "newsletter", "email", "new_campaign")

        assert "utm_campaign=new_campaign" in result
        assert "utm_campaign=old_campaign" not in result

    def test_existing_utm_source_preserved(self):
        """Existing utm_source is not overwritten."""
        url = "https://example.com/page?utm_source=existing_source"
        result = add_utm_parameters(url, "newsletter", "email", "summer2024")

        assert "utm_source=existing_source" in result
        assert "utm_source=newsletter" not in result

    def test_empty_url_returns_empty(self):
        """An empty URL is returned as-is."""
        assert add_utm_parameters("", "src", "med", "camp") == ""


# ════════════════════════════════════════════════════════════════════════
# 5. DEAL TIER CLASSIFICATION
# ════════════════════════════════════════════════════════════════════════
class TestDealTierClassification:
    """Verify _deal_tier_for returns correct tiers for different deal types."""

    def test_lightning_deal_is_glitch(self):
        """Lightning deals are classified as 'glitch'."""
        deal = AmazonDeal(asin="B123", title="Test", deal_price=10, deal_type="lightning")
        assert _deal_tier_for(deal) == "glitch"

    def test_movers_shakers_is_trending(self):
        """Movers & Shakers are classified as 'trending'."""
        deal = AmazonDeal(asin="B123", title="Test", deal_price=10, deal_type="movers_shakers")
        assert _deal_tier_for(deal) == "trending"

    def test_hot_new_release_is_trending(self):
        """Hot New Releases are classified as 'trending'."""
        deal = AmazonDeal(asin="B123", title="Test", deal_price=10, deal_type="hot_new_release")
        assert _deal_tier_for(deal) == "trending"

    def test_regular_deal_is_clearance(self):
        """Regular deals default to 'clearance'."""
        deal = AmazonDeal(asin="B123", title="Test", deal_price=10, deal_type="deal")
        assert _deal_tier_for(deal) == "clearance"

    def test_deal_of_day_is_clearance(self):
        """Deal of the day falls through to 'clearance'."""
        deal = AmazonDeal(asin="B123", title="Test", deal_price=10, deal_type="deal_of_day")
        assert _deal_tier_for(deal) == "clearance"

    def test_coupon_deal_is_clearance(self):
        """Coupon deals fall through to 'clearance'."""
        deal = AmazonDeal(asin="B123", title="Test", deal_price=10, deal_type="coupon")
        assert _deal_tier_for(deal) == "clearance"
