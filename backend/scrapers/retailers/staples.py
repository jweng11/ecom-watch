"""Staples Canada scraper — staples.ca digital flyers."""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class StaplesScraper(BaseScraper):
    retailer_slug = "staples"
    retailer_name = "Staples"

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Staples weekly flyer page."""
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)
        # Flyer pages may embed an iframe or require waiting for content
        try:
            await page.wait_for_selector(".flyer-container, .flyer-frame, iframe, .product-listing", timeout=15_000)
        except Exception:
            logger.info(f"[{self.retailer_slug}] Flyer container not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Staples cookie/survey popups."""
        try:
            consent = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept All')")
            if await consent.first.is_visible(timeout=3000):
                await consent.first.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        # Survey popup
        try:
            no_thanks = page.locator("button:has-text('No Thanks'), button:has-text('No, thanks')")
            if await no_thanks.first.is_visible(timeout=2000):
                await no_thanks.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass
