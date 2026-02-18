"""Costco Canada scraper — costco.ca laptop deals."""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CostcoScraper(BaseScraper):
    retailer_slug = "costco"
    retailer_name = "Costco"

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Costco's laptop category page."""
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)
        try:
            await page.wait_for_selector(".product-list, .product-tile-set, .product", timeout=15_000)
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product listing not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Costco location/membership prompts."""
        await super().dismiss_popups(page)
        # Costco sometimes shows delivery location picker
        try:
            close = page.locator("button:has-text('Continue'), button:has-text('Set Location')")
            if await close.first.is_visible(timeout=2000):
                await close.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass
