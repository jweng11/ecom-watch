"""Best Buy Canada scraper — bestbuy.ca laptop deals and top deals."""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BestBuyScraper(BaseScraper):
    retailer_slug = "bestbuy"
    retailer_name = "Best Buy"

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Best Buy's laptop deals page."""
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)
        # Wait for product grid to appear
        try:
            await page.wait_for_selector("[class*='productList'], [class*='product-grid'], .x-product", timeout=15_000)
        except Exception:
            logger.info(f"[{self.retailer_slug}] Product grid selector not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Best Buy cookie consent and newsletter popups."""
        # Cookie consent
        try:
            consent = page.locator("button:has-text('Accept All Cookies'), button:has-text('Accept')")
            if await consent.first.is_visible(timeout=3000):
                await consent.first.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        # Newsletter / sign-up modal
        try:
            close_btn = page.locator("[class*='modal'] button[class*='close'], [aria-label='Close']")
            if await close_btn.first.is_visible(timeout=2000):
                await close_btn.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def scroll_for_content(self, page: Page) -> None:
        """Scroll to load lazy product cards on Best Buy."""
        await super().scroll_for_content(page)
        # Best Buy often has "Show More" buttons
        try:
            show_more = page.locator("button:has-text('Show More'), a:has-text('Show More')")
            for _ in range(3):
                if await show_more.first.is_visible(timeout=2000):
                    await show_more.first.click()
                    await asyncio.sleep(2)
                else:
                    break
        except Exception:
            pass
