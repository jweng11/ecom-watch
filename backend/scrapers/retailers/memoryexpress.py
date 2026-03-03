"""Memory Express scraper — memoryexpress.com laptop deals.

Memory Express uses Cloudflare protection which shows "Just a moment..." challenge pages.
The stealth + challenge wait strategy should handle this in many cases.
"""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

MEMORYEXPRESS_LAPTOPS_URL = "https://www.memoryexpress.com/Category/LaptopsNotebooks"


class MemoryExpressScraper(BaseScraper):
    retailer_slug = "memoryexpress"
    retailer_name = "Memory Express"
    stealth_enabled = True  # Required — Cloudflare challenge blocks without stealth

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Memory Express laptop category with Cloudflare handling."""
        response = await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)

        # Cloudflare challenge detection and wait
        if response and response.status in (403, 503):
            logger.warning(f"[{self.retailer_slug}] Access denied (status {response.status})")

        if await self.detect_cloudflare_challenge(page):
            resolved = await self.wait_for_challenge_resolution(page, timeout_s=15)
            if not resolved:
                logger.error(f"[{self.retailer_slug}] Cloudflare challenge did not resolve")
                return

        if self._use_stealth:
            await self.random_delay(2, 5)

        try:
            await page.wait_for_selector(
                ".c-shca-icon-item, .PIV_CompareLine, .PROD_header, .c-shca-list",
                timeout=15_000,
            )
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product listing not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Memory Express popups."""
        await super().dismiss_popups(page)
