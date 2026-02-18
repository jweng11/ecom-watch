"""The Source scraper — thesource.ca laptop deals."""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class TheSourceScraper(BaseScraper):
    retailer_slug = "thesource"
    retailer_name = "The Source"

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to The Source laptop category page."""
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)
        try:
            await page.wait_for_selector(".product-listing, .plp-card, .product-tile", timeout=15_000)
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product listing not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle The Source popups and cookie consent."""
        await super().dismiss_popups(page)
        # The Source sometimes has age gate or newsletter popup
        try:
            close = page.locator("[class*='popup'] .close, button:has-text('No Thanks')")
            if await close.first.is_visible(timeout=2000):
                await close.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass
