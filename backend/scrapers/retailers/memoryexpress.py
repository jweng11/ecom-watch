"""Memory Express scraper — memoryexpress.com laptop deals."""

import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class MemoryExpressScraper(BaseScraper):
    retailer_slug = "memoryexpress"
    retailer_name = "Memory Express"

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Memory Express laptop category."""
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)
        try:
            await page.wait_for_selector(".c-shca-icon-item, .PIV_CompareLine, .PROD_header", timeout=15_000)
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product listing not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Memory Express popups."""
        await super().dismiss_popups(page)
