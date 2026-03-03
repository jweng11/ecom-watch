"""Best Buy Canada scraper — bestbuy.ca laptop deals and top deals.

Best Buy uses Akamai WAF which aggressively blocks automated access (403 "Access Denied").
Stealth mode with longer delays is required. Even with stealth, success is not guaranteed.
"""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Best Buy laptop deals — verified URL (returns 403 without stealth, but the path is valid)
BESTBUY_LAPTOP_DEALS_URL = "https://www.bestbuy.ca/en-ca/collection/top-deals-laptops/36582"


class BestBuyScraper(BaseScraper):
    retailer_slug = "bestbuy"
    retailer_name = "Best Buy"
    stealth_enabled = True  # Required — Akamai WAF blocks without stealth

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Best Buy's laptop deals page with stealth precautions."""
        # Human-like mouse movement before navigation
        if self._use_stealth:
            await self.random_mouse_movement(page)

        response = await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)

        # Check for Akamai block (returns 403 with "Access Denied" page)
        if response and response.status == 403:
            title = await page.title()
            logger.warning(f"[{self.retailer_slug}] Akamai WAF block detected (403, title: {title})")
            # Wait briefly in case it's a soft challenge
            await asyncio.sleep(3)

        # Extra delay for Best Buy — they monitor request timing
        if self._use_stealth:
            await self.random_delay(3, 6)

        # Wait for product grid
        try:
            await page.wait_for_selector(
                "[class*='productList'], [class*='product-grid'], .x-product", timeout=15_000
            )
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product grid selector not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Best Buy cookie consent and newsletter popups."""
        try:
            consent = page.locator("button:has-text('Accept All Cookies'), button:has-text('Accept')")
            if await consent.first.is_visible(timeout=3000):
                await consent.first.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        try:
            close_btn = page.locator("[class*='modal'] button[class*='close'], [aria-label='Close']")
            if await close_btn.first.is_visible(timeout=2000):
                await close_btn.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def scroll_for_content(self, page: Page) -> None:
        """Scroll to load lazy product cards on Best Buy with human-like behavior."""
        await super().scroll_for_content(page)

        # Best Buy often has "Show More" buttons
        try:
            show_more = page.locator("button:has-text('Show More'), a:has-text('Show More')")
            for _ in range(3):
                if await show_more.first.is_visible(timeout=2000):
                    if self._use_stealth:
                        await self.random_delay(1, 3)
                    await show_more.first.click()
                    await asyncio.sleep(2)
                else:
                    break
        except Exception:
            pass
