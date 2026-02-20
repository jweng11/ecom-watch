"""Walmart Canada scraper — walmart.ca laptop rollbacks and deals.

Walmart uses PerimeterX bot detection which is very aggressive. Stealth alone may not
be sufficient. We use maximum human-like behavior (long delays, scrolling, mouse movements)
to maximize our chances.
"""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

WALMART_LAPTOPS_URL = "https://www.walmart.ca/browse/electronics/laptops/10003/30622"


class WalmartScraper(BaseScraper):
    retailer_slug = "walmart"
    retailer_name = "Walmart"
    stealth_enabled = True  # Required — PerimeterX blocks without stealth

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Walmart's laptop category with maximum human-like behavior."""
        # Pre-navigation mouse movement
        if self._use_stealth:
            await self.random_mouse_movement(page)
            await self.random_delay(1, 3)

        response = await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)

        # PerimeterX may show a challenge page
        if await self.detect_cloudflare_challenge(page) or await self.detect_access_denied(page, response):
            logger.warning(f"[{self.retailer_slug}] PerimeterX/WAF challenge detected")
            await self.wait_for_challenge_resolution(page, timeout_s=15)

        # Extended delay — Walmart monitors timing closely
        if self._use_stealth:
            await self.random_delay(4, 8)
            await self.random_mouse_movement(page)

        try:
            await page.wait_for_selector(
                "[data-testid='product-tile'], .product-tile, .search-result-listview-items",
                timeout=15_000,
            )
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product tiles not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Walmart cookie consent and location prompts."""
        try:
            consent = page.locator("button:has-text('Accept'), button:has-text('Accept All Cookies')")
            if await consent.first.is_visible(timeout=3000):
                await consent.first.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        try:
            close = page.locator("[data-testid='flyout-close'], button[aria-label='close']")
            if await close.first.is_visible(timeout=2000):
                await close.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def scroll_for_content(self, page: Page) -> None:
        """Scroll through Walmart product listings with human-like behavior."""
        # Use human scroll from base (stealth-aware)
        await super().scroll_for_content(page)

        if self._use_stealth:
            await self.random_delay(2, 4)

        try:
            next_page = page.locator("[aria-label='Next Page'], a:has-text('Next page')")
            if await next_page.first.is_visible(timeout=2000):
                logger.info(f"[{self.retailer_slug}] Additional pages available (capturing first page only)")
        except Exception:
            pass
