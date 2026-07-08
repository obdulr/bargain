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
from app.services.notification_service import distribute_deal, DealInfo, get_sms_recipients

logger = logging.getLogger(__name__)


class ScanScheduler:
    """Background asyncio task scheduler for periodic arbitrage scans."""

    def __init__(self, interval_minutes: int = None):
        self.interval_minutes = interval_minutes or settings.SCAN_INTERVAL_MINUTES
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_scan_at: Optional[datetime] = None
        self._next_scan_at: Optional[datetime] = None
        self._last_scan_status: str = "never"
        self._last_error: Optional[str] = None

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
        }

    def start(self) -> bool:
        """Start the background scanner. Returns True if started, False if already running."""
        if self._running and self._task and not self._task.done():
            logger.warning("Scheduler is already running")
            return False

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Scan scheduler started (interval: {self.interval_minutes}min)")
        return True

    def stop(self) -> bool:
        """Stop the background scanner. Returns True if stopped, False if not running."""
        if not self._running:
            logger.warning("Scheduler is not running")
            return False

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
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
            sms_recipients = get_sms_recipients(db)

            for opp in opportunities:
                if not opp.is_profitable:
                    continue

                # Save the deal to the database
                deal = _save_opportunity(db, opp)
                db.commit()

                # Distribute to all notification channels (Discord, Telegram, Twitter, Facebook, SMS)
                deal_info = DealInfo.from_opportunity(opp)
                try:
                    await distribute_deal(deal_info, db, sms_recipients=sms_recipients)
                except Exception as e:
                    logger.error(f"Notification distribution failed for {opp.asin}: {e}")

                # Create email alerts for each active user
                for user in users:
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
