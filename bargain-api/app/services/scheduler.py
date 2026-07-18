"""
Scheduled Scanner — Phase 1

A background asyncio task scheduler that runs periodic arbitrage scans.
No Celery needed for MVP — uses asyncio tasks.

Flow:
1. Every SCAN_INTERVAL_MINUTES, runs scan_amazon_for_arbitrage()
2. For each profitable deal found, triggers the alert service
3. Tracks scan runs in the ScanRun table
4. Handles errors gracefully (failed scans don't crash the scheduler)
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import logging

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import ScanRun, User, ArbitrageDeal
from app.services.arbitrage import scan_amazon_for_arbitrage, find_arbitrage_for_asin, ArbitrageOpportunity
from app.services.profit_calculator import Platform
from app.services.alert_service import create_alert_for_opportunity
from app.services.notification_service import distribute_deal, DealInfo, get_sms_recipients, user_subscribed_to_niche

logger = logging.getLogger(__name__)


class ScanScheduler:
    """Background asyncio task scheduler for periodic arbitrage scans.

    Also runs a deal scraping + X posting task every 2 hours that:
    1. Scrapes Amazon Gold Box + RSS feeds for new deals
    2. Posts the top deals to X via Make.com webhook (runs 24/7, no computer needed)
    """

    def __init__(self, interval_minutes: int = None):
        self.interval_minutes = interval_minutes or settings.SCAN_INTERVAL_MINUTES
        self._task: Optional[asyncio.Task] = None
        self._deal_task: Optional[asyncio.Task] = None
        self._engagement_task: Optional[asyncio.Task] = None
        self._running = False
        self._last_scan_at: Optional[datetime] = None
        self._next_scan_at: Optional[datetime] = None
        self._last_scan_status: str = "never"
        self._last_error: Optional[str] = None
        self._last_deal_scrape_at: Optional[datetime] = None
        self._last_engagement_at: Optional[datetime] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_scan_at(self) -> Optional[datetime]:
        return self._last_scan_at

    @property
    def next_scan_at(self) -> Optional[datetime]:
        return self._next_scan_at

    @property
    def last_scan_status(self) -> str:
        return self._last_scan_status

    def get_status(self) -> dict:
        """Get the current scheduler status."""
        return {
            "running": self._running,
            "interval_minutes": self.interval_minutes,
            "last_scan_at": self._last_scan_at.isoformat() if self._last_scan_at else None,
            "next_scan_at": self._next_scan_at.isoformat() if self._next_scan_at else None,
            "last_scan_status": self._last_scan_status,
            "last_error": self._last_error,
            "last_deal_scrape_at": self._last_deal_scrape_at.isoformat() if self._last_deal_scrape_at else None,
            "last_engagement_at": self._last_engagement_at.isoformat() if self._last_engagement_at else None,
        }

    def start(self) -> bool:
        """Start the background scanner. Returns True if started, False if already running."""
        if self._running and self._task and not self._task.done():
            logger.warning("Scheduler is already running")
            return False

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        # Start the deal scraping + X posting loop (every 2 hours)
        self._deal_task = asyncio.create_task(self._run_deal_scrape_loop())
        # Start the X engagement automation loop (every 30 minutes) if enabled
        if getattr(settings, "ENGAGEMENT_ENABLED", False):
            self._engagement_task = asyncio.create_task(self._run_engagement_loop())
            logger.info(
                f"Scan scheduler started (interval: {self.interval_minutes}min, "
                f"deal scrape: every 120min, engagement: every 30min)"
            )
        else:
            logger.info(
                f"Scan scheduler started (interval: {self.interval_minutes}min, "
                f"deal scrape: every 120min, engagement: disabled)"
            )
        return True

    def stop(self) -> bool:
        """Stop the background scanner. Returns True if stopped, False if not running."""
        if not self._running:
            logger.warning("Scheduler is not running")
            return False

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        if self._deal_task and not self._deal_task.done():
            self._deal_task.cancel()
        if self._engagement_task and not self._engagement_task.done():
            self._engagement_task.cancel()
        self._next_scan_at = None
        logger.info("Scan scheduler stopped")
        return True

    async def _run_loop(self):
        """Main scheduler loop — runs scans at the configured interval."""
        logger.info("Scheduler loop started")

        # Run an initial scan immediately
        await self._run_scan()

        while self._running:
            # Calculate sleep time until next scan
            self._next_scan_at = datetime.utcnow() + timedelta(minutes=self.interval_minutes)
            sleep_seconds = self.interval_minutes * 60

            try:
                await asyncio.sleep(sleep_seconds)
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break

            if not self._running:
                break

            await self._run_scan()

        logger.info("Scheduler loop ended")
        self._next_scan_at = None

    async def _run_deal_scrape_loop(self):
        """Background loop that scrapes deals and posts to X every 2 hours.

        1. Scrapes Amazon Gold Box + RSS feeds (Slickdeals, TechBargains, etc.)
        2. Posts top 3 new deals to X via Make.com webhook
        3. Runs completely on the server — no computer or browser needed
        """
        DEAL_SCRAPE_INTERVAL = 120  # minutes
        logger.info("Deal scrape + X posting loop started (every 120min)")

        while self._running:
            try:
                await self._scrape_and_post_to_x()
            except Exception as e:
                logger.error(f"Deal scrape loop error: {e}", exc_info=True)

            # Wait for next interval
            try:
                await asyncio.sleep(DEAL_SCRAPE_INTERVAL * 60)
            except asyncio.CancelledError:
                logger.info("Deal scrape loop cancelled")
                break

    async def _run_engagement_loop(self):
        """Background loop that runs the X engagement bot every 30 minutes.

        Likes, replies to, and follows deal-hunting accounts on X to grow the
        @bargain4huntrs account. Only runs when ENGAGEMENT_ENABLED is True and
        the required X API v2 tokens are configured.
        """
        ENGAGEMENT_INTERVAL = 30  # minutes
        logger.info("X engagement loop started (every 30min)")

        while self._running:
            try:
                from app.services.engagement_bot import run_engagement_cycle, is_configured

                if not is_configured():
                    logger.info("Engagement bot not configured, skipping cycle")
                else:
                    await run_engagement_cycle()
                    self._last_engagement_at = datetime.utcnow()
            except Exception as e:
                logger.error(f"Engagement loop error: {e}", exc_info=True)

            # Wait for next interval
            try:
                await asyncio.sleep(ENGAGEMENT_INTERVAL * 60)
            except asyncio.CancelledError:
                logger.info("Engagement loop cancelled")
                break

    async def _scrape_and_post_to_x(self):
        """Scrape deals from all sources and post new ones to X via Buffer API."""
        self._last_deal_scrape_at = datetime.utcnow()
        logger.info("Starting deal scrape + X posting cycle...")

        from app.services.amazon_deals_scraper import scrape_amazon_deals, save_deals_to_database
        from app.services.rss_deals_scraper import scrape_all_rss_feeds, save_rss_deals_to_database
        from app.services.impact_api import fetch_all_impact_deals, _is_configured as impact_configured
        from app.services.x_poster import post_deal_to_x, is_configured as x_configured

        db = SessionLocal()
        try:
            # Scrape Amazon Gold Box
            try:
                amazon_deals = await scrape_amazon_deals(max_deals=50)
                amazon_saved = save_deals_to_database(amazon_deals, db)
                logger.info(f"Amazon: {len(amazon_deals)} found, {amazon_saved} saved")
            except Exception as e:
                logger.error(f"Amazon scrape failed: {e}")

            # Scrape RSS feeds
            try:
                rss_deals = await scrape_all_rss_feeds(min_discount=40)
                rss_saved = save_rss_deals_to_database(rss_deals, db)
                logger.info(f"RSS: {len(rss_deals)} found, {rss_saved} saved")
            except Exception as e:
                logger.error(f"RSS scrape failed: {e}")

            # Scrape Impact.com product catalogs
            if impact_configured():
                try:
                    impact_deals = await fetch_all_impact_deals()
                    impact_saved = 0
                    for deal in impact_deals:
                        try:
                            if not deal.get("deal_price") or not deal.get("title"):
                                continue
                            deal_id = f"impact_{deal.get('campaign_id', '')}_{abs(hash(deal.get('title', '')))}"[:36]
                            existing = db.query(ArbitrageDeal).filter(
                                ArbitrageDeal.asin == deal_id,
                                ArbitrageDeal.status == "active",
                            ).first()
                            if existing:
                                continue
                            orig = deal.get("original_price") or 0
                            buy = deal.get("deal_price") or 0
                            if not buy or buy <= 0:
                                continue
                            tier = "glitch" if (deal.get("discount_percent", 0) or 0) >= 75 else "clearance"
                            new_deal = ArbitrageDeal(
                                asin=deal_id,
                                title=deal.get("title", "")[:500],
                                image_url=deal.get("image_url"),
                                buy_url=deal.get("deal_url"),
                                buy_platform=deal.get("retailer", "unknown"),
                                retailer=deal.get("retailer", "unknown"),
                                deal_source="online",
                                buy_price=buy,
                                sell_platform="impact",
                                sell_price=orig if orig else buy,
                                historical_avg=orig if orig else buy,
                                deal_tier=tier,
                                net_profit=(orig - buy) if orig else 0,
                                roi=float((orig - buy) / orig) if orig and orig > 0 else 0,
                                is_profitable=True,
                                status="active",
                                detected_at=datetime.utcnow(),
                            )
                            db.add(new_deal)
                            db.commit()
                            impact_saved += 1
                        except Exception:
                            db.rollback()
                    logger.info(f"Impact: {len(impact_deals)} found, {impact_saved} saved")
                except Exception as e:
                    logger.error(f"Impact scrape failed: {e}")

            # Post new deals to social media via Buffer API
            # ONLY post deals with affiliate tracking links
            if x_configured():
                # Fetch more deals than needed, then filter for affiliate links
                candidate_deals = (
                    db.query(ArbitrageDeal)
                    .filter(
                        ArbitrageDeal.status == "active",
                        ArbitrageDeal.is_profitable == True,
                        ArbitrageDeal.alerted_at == None,
                    )
                    .order_by(ArbitrageDeal.detected_at.desc())
                    .limit(20)
                    .all()
                )

                # Only post deals that have affiliate links
                affiliate_domains = ["sjv.io", "7eer.net", "pxf.io", "evyy.net",
                    "vneoga.net", "elfm.net", "eyjo.net", "gqco.net", "hmxg.net",
                    "ijrn.net", "jewn.net", "jyeh.net", "mtko.net", "tcux.net",
                    "zlvv.net", "goto.walmart.com", "affiliates.abebooks.com",
                    "tag=bargain0ae", "campid=", "affid="]
                new_deals = []
                for d in candidate_deals:
                    url = (d.buy_url or "").lower()
                    if any(x in url for x in affiliate_domains):
                        new_deals.append(d)
                    if len(new_deals) >= 3:
                        break

                if new_deals:
                    logger.info(f"Posting {len(new_deals)} affiliate deals to social media")
                    posted = 0
                    for deal in new_deals:
                        discount = 0
                        if deal.historical_avg and deal.historical_avg > deal.buy_price:
                            discount = int(round((1 - float(deal.buy_price) / float(deal.historical_avg)) * 100))

                        result = await post_deal_to_x(
                            title=deal.title,
                            deal_price=float(deal.buy_price),
                            original_price=float(deal.historical_avg) if deal.historical_avg else None,
                            discount_percent=discount,
                            retailer=getattr(deal, "retailer", None) or "amazon",
                            deal_url=deal.buy_url or "",
                            deal_tier=deal.deal_tier,
                            image_url=deal.image_url,
                        )

                        if result.get("status") == "success":
                            posted += 1
                            deal.alerted_at = datetime.utcnow()
                            db.commit()
                            logger.info(f"  Posted: {deal.title[:50]}")
                        else:
                            logger.warning(f"  Post failed: {result.get('error')}")

                        # Small delay between posts
                        await asyncio.sleep(5)

                    logger.info(f"Posting complete: {posted}/{len(new_deals)} posted")
                else:
                    logger.info("No new affiliate deals to post")
            else:
                logger.info("Social posting not configured (BUFFER_API_KEY not set)")

        finally:
            db.close()

    async def _run_scan(self):
        """Run a single scan cycle."""
        self._last_scan_at = datetime.utcnow()
        logger.info("Starting scheduled scan...")

        db = SessionLocal()
        scan_run = ScanRun(
            scan_type="amazon_ebay_scheduled",
            status="running",
        )
        db.add(scan_run)
        db.commit()
        db.refresh(scan_run)

        try:
            # Run the bulk scan
            opportunities = await scan_amazon_for_arbitrage(
                category="",
                min_discount=Decimal("0.50"),
                max_price=Decimal("500.00"),
                limit=20,
                sell_platform=Platform.EBAY,
            )

            scan_run.products_scanned = 20
            scan_run.deals_found = len(opportunities)

            # Save profitable deals and create alerts for all active users
            deals_alerted = 0
            users = db.query(User).filter(User.is_active == True).all()

            for opp in opportunities:
                if not opp.is_profitable:
                    continue

                # Save the deal to the database
                deal = _save_opportunity(db, opp)
                db.commit()

                # Distribute to all notification channels (Discord, Telegram, Twitter, Facebook, SMS)
                deal_info = DealInfo.from_opportunity(opp)
                # SMS recipients are filtered by niche subscription: a user with
                # no subscriptions receives all niches; otherwise only their picks.
                sms_recipients = get_sms_recipients(db, niche=opp.niche)
                try:
                    await distribute_deal(deal_info, db, sms_recipients=sms_recipients)
                except Exception as e:
                    logger.error(f"Notification distribution failed for {opp.asin}: {e}")

                # Create email alerts only for users subscribed to this niche
                # (users with no niche subscription receive all niches)
                for user in users:
                    if not user_subscribed_to_niche(user, opp.niche):
                        continue
                    alert = create_alert_for_opportunity(db, user, opp)
                    if alert:
                        deals_alerted += 1

            scan_run.deals_alerted = deals_alerted
            scan_run.completed_at = datetime.utcnow()
            scan_run.status = "completed"
            db.commit()

            self._last_scan_status = "completed"
            self._last_error = None
            logger.info(
                f"Scheduled scan completed: {len(opportunities)} deals found, "
                f"{deals_alerted} alerts sent"
            )

        except Exception as e:
            scan_run.status = "failed"
            scan_run.error = str(e)
            scan_run.completed_at = datetime.utcnow()
            db.commit()

            self._last_scan_status = "failed"
            self._last_error = str(e)
            logger.error(f"Scheduled scan failed: {e}", exc_info=True)

        finally:
            db.close()


def _save_opportunity(db, opp: ArbitrageOpportunity) -> ArbitrageDeal:
    """Save an ArbitrageOpportunity to the database (dedup within 24h)."""
    cutoff = datetime.utcnow() - timedelta(hours=24)
    existing = db.query(ArbitrageDeal).filter(
        ArbitrageDeal.asin == opp.asin,
        ArbitrageDeal.detected_at >= cutoff,
    ).first()

    if existing:
        # Update existing deal with latest data
        existing.buy_price = opp.buy_price
        existing.sell_price = opp.sell_price
        if opp.profit:
            existing.net_profit = opp.profit.net_profit
            existing.roi = opp.profit.roi
            existing.total_costs = opp.profit.total_costs
            existing.platform_fee = opp.profit.platform_fee
        existing.is_profitable = opp.is_profitable
        existing.detected_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    deal = ArbitrageDeal(
        asin=opp.asin,
        title=opp.title,
        image_url=opp.image_url,
        buy_url=opp.buy_url,
        buy_price=opp.buy_price,
        sell_price=opp.sell_price,
        historical_avg=opp.historical_avg,
        discrepancy=opp.discrepancy,
        deal_tier=opp.deal_tier,
        net_profit=opp.profit.net_profit if opp.profit else None,
        roi=opp.profit.roi if opp.profit else None,
        total_costs=opp.profit.total_costs if opp.profit else None,
        platform_fee=opp.profit.platform_fee if opp.profit else None,
        bsr=opp.bsr,
        category=opp.category,
        is_profitable=opp.is_profitable,
        status="active",
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


# Global scheduler instance
scheduler = ScanScheduler()
