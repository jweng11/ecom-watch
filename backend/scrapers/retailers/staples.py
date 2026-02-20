"""Staples Canada scraper — staples.ca laptop listings.

Staples uses Cloudflare which blocks automated access (403).
The previous flyer URL (/a/content/flyers) pointed to an image-based flyer viewer
with no scrapeable HTML product data.

Updated to use the laptops collection page: /collections/laptops-90
Note: Cloudflare protection is aggressive — this scraper may still be blocked.
"""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Laptops collection page (has HTML product data, unlike the flyer viewer)
STAPLES_LAPTOPS_URL = "https://www.staples.ca/collections/laptops-90"


class StaplesScraper(BaseScraper):
    retailer_slug = "staples"
    retailer_name = "Staples"
    stealth_enabled = True  # Required — Cloudflare blocks without stealth

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Staples laptop collection page."""
        response = await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)

        # Cloudflare challenge handling
        if await self.detect_cloudflare_challenge(page):
            await self.wait_for_challenge_resolution(page, timeout_s=15)

        if self._use_stealth:
            await self.random_delay(2, 5)

        try:
            await page.wait_for_selector(".product-listing, .product-tile, .collection-products", timeout=15_000)
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product listing not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Staples cookie/survey popups."""
        try:
            consent = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept All')")
            if await consent.first.is_visible(timeout=3000):
                await consent.first.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        try:
            no_thanks = page.locator("button:has-text('No Thanks'), button:has-text('No, thanks')")
            if await no_thanks.first.is_visible(timeout=2000):
                await no_thanks.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass
