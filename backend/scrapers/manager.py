"""Scrape manager — orchestrates scrape runs across retailers."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database.models import ScrapeRun, Retailer
from scrapers.base import ScrapeResult
from scrapers.retailers import SCRAPER_REGISTRY
from scrapers.utils.storage import save_screenshot, save_html, save_metadata

logger = logging.getLogger(__name__)

# Track whether a scrape is currently running (simple lock for single-process app)
_current_scrape: Optional[dict] = None


def get_scrape_status() -> dict:
    """Return current scraping status."""
    if _current_scrape is None:
        return {"running": False, "current_retailer": None, "progress": 0.0, "retailers_completed": 0, "retailers_total": 0}
    return {**_current_scrape, "running": True}


def claim_scrape_lock() -> bool:
    """
    Atomically check-and-set the scrape lock. Returns True if lock was acquired.

    Call this from the API handler *before* queuing the background task to prevent
    TOCTOU races where two rapid requests both pass the get_scrape_status() check.
    """
    global _current_scrape
    if _current_scrape is not None:
        return False
    _current_scrape = {
        "current_retailer": None,
        "progress": 0.0,
        "retailers_completed": 0,
        "retailers_total": 0,
    }
    return True


def release_scrape_lock():
    """Release the scrape lock if it needs to be freed without running a scrape."""
    global _current_scrape
    _current_scrape = None


async def run_scrape(retailer_slug: str, trigger_type: str, db: Session) -> list[int]:
    """
    Run a scrape for one retailer or all enabled retailers.

    Args:
        retailer_slug: Specific retailer slug, or "all" for all enabled retailers
        trigger_type: "manual" or "scheduled"
        db: SQLAlchemy session

    Returns:
        List of ScrapeRun IDs created
    """
    global _current_scrape

    # Lock should already be claimed via claim_scrape_lock() before queuing.
    # Guard here as a safety net for direct callers.
    if _current_scrape is None:
        if not claim_scrape_lock():
            raise RuntimeError("A scrape is already in progress")

    # Wrap entire body in try/finally to guarantee lock release on ALL exit paths
    # (early returns, ValueErrors, unexpected exceptions).
    try:
        # Determine which retailers to scrape
        if retailer_slug == "all":
            retailers = db.query(Retailer).filter(Retailer.scrape_enabled.is_(True)).all()
        else:
            retailer = db.query(Retailer).filter(Retailer.slug == retailer_slug).first()
            if not retailer:
                raise ValueError(f"Unknown retailer: {retailer_slug}")
            if not retailer.scrape_enabled:
                raise ValueError(f"Retailer {retailer_slug} is disabled for scraping")
            retailers = [retailer]

        if not retailers:
            logger.warning("No enabled retailers to scrape")
            return []

        run_ids = []
        _current_scrape["retailers_total"] = len(retailers)

        for idx, retailer in enumerate(retailers):
            _current_scrape["current_retailer"] = retailer.name
            _current_scrape["progress"] = idx / len(retailers)

            run_id = await _scrape_single_retailer(retailer, trigger_type, db)
            run_ids.append(run_id)

            _current_scrape["retailers_completed"] = idx + 1
            _current_scrape["progress"] = (idx + 1) / len(retailers)

            # Rate limit between retailers
            if idx < len(retailers) - 1:
                logger.info(f"Waiting 5s before next retailer...")
                await asyncio.sleep(5)

        return run_ids

    finally:
        _current_scrape = None


async def _scrape_single_retailer(retailer: Retailer, trigger_type: str, db: Session) -> int:
    """
    Scrape a single retailer: create ScrapeRun, execute scraper, update record.
    Returns the ScrapeRun ID.
    """
    # Create the ScrapeRun record
    scrape_run = ScrapeRun(
        retailer=retailer.name,
        status="running",
        trigger_type=trigger_type,
    )
    db.add(scrape_run)
    db.commit()
    db.refresh(scrape_run)
    run_id = scrape_run.id

    logger.info(f"[{retailer.slug}] Starting scrape run #{run_id}")

    # Get the scraper class
    scraper_class = SCRAPER_REGISTRY.get(retailer.slug)
    if scraper_class is None:
        scrape_run.status = "failed"
        scrape_run.error_message = f"No scraper registered for {retailer.slug}"
        scrape_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.error(f"[{retailer.slug}] No scraper registered")
        return run_id

    # Execute the scraper
    scraper = scraper_class(
        base_url=retailer.base_url,
        scrape_config=retailer.scrape_config,
    )

    try:
        result: ScrapeResult = await scraper.run()
    except Exception as e:
        result = ScrapeResult(
            status="failed",
            error_message=f"Unexpected error: {type(e).__name__}: {e}",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        logger.error(f"[{retailer.slug}] Scraper raised exception: {e}")

    # Save files if scrape captured data
    screenshot_path = None
    html_path = None

    if result.screenshot_bytes:
        try:
            screenshot_path = save_screenshot(retailer.slug, result.screenshot_bytes)
        except Exception as e:
            logger.error(f"[{retailer.slug}] Failed to save screenshot: {e}")

    if result.html_content:
        try:
            html_path = save_html(retailer.slug, result.html_content)
        except Exception as e:
            logger.error(f"[{retailer.slug}] Failed to save HTML: {e}")

    # Save metadata
    try:
        save_metadata(retailer.slug, {
            "scrape_run_id": run_id,
            "retailer": retailer.name,
            "slug": retailer.slug,
            "url": result.page_url or retailer.base_url,
            "title": result.page_title,
            "status": result.status,
            "started_at": result.started_at,
            "completed_at": result.completed_at,
        })
    except Exception as e:
        logger.warning(f"[{retailer.slug}] Failed to save metadata: {e}")

    # Update the ScrapeRun record
    scrape_run = db.get(ScrapeRun, run_id)
    if scrape_run is None:
        logger.error(f"[{retailer.slug}] ScrapeRun #{run_id} unexpectedly missing from database")
        return run_id
    scrape_run.status = result.status
    scrape_run.completed_at = result.completed_at or datetime.now(timezone.utc)
    scrape_run.screenshot_path = screenshot_path
    scrape_run.html_path = html_path
    scrape_run.items_found = result.items_found
    scrape_run.error_message = result.error_message
    db.commit()

    # Update retailer's last_scraped timestamp
    if result.status in ("completed", "partial"):
        retailer.last_scraped = datetime.now(timezone.utc)
        db.commit()

    logger.info(f"[{retailer.slug}] Scrape run #{run_id} finished with status: {result.status}")
    return run_id
