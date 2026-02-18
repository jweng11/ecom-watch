"""Canada Computers scraper — canadacomputers.com laptop deals."""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CanadaComputersScraper(BaseScraper):
    retailer_slug = "canadacomputers"
    retailer_name = "Canada Computers"

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Canada Computers promotions page."""
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)
        try:
            await page.wait_for_selector(".productTemplate, .product-list, .products-grid", timeout=15_000)
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product grid not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Canada Computers popups."""
        await super().dismiss_popups(page)
        # Location selector
        try:
            close = page.locator(".modal .close, button:has-text('Continue Shopping')")
            if await close.first.is_visible(timeout=2000):
                await close.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass
