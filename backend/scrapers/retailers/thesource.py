"""The Source scraper — thesource.ca laptop deals.

The Source is a Bell subsidiary (formerly RadioShack). The site appears to still be
operational and may not have aggressive bot protection. URL verified via search results.
"""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Updated URL from search results — includes all laptops
THESOURCE_LAPTOPS_URL = "https://www.thesource.ca/en-ca/computers-tablets/laptops/c/scc-1-2"


class TheSourceScraper(BaseScraper):
    retailer_slug = "thesource"
    retailer_name = "The Source"
    stealth_enabled = True  # Enabled as precaution, though may not be strictly needed

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to The Source laptop category page."""
        response = await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)

        # Check if site redirects to bestbuy.ca or bell.ca
        current_url = page.url
        if "bestbuy.ca" in current_url or "bell.ca" in current_url:
            logger.warning(
                f"[{self.retailer_slug}] Site redirected to {current_url} — "
                "The Source may have been absorbed by Best Buy/Bell"
            )

        if self._use_stealth:
            await self.random_delay(2, 4)

        try:
            await page.wait_for_selector(
                ".product-listing, .plp-card, .product-tile, .product-grid", timeout=15_000
            )
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product listing not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle The Source popups and cookie consent."""
        await super().dismiss_popups(page)
        try:
            close = page.locator("[class*='popup'] .close, button:has-text('No Thanks')")
            if await close.first.is_visible(timeout=2000):
                await close.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass
