"""Amazon Canada scraper — amazon.ca laptop bestsellers and deals.

Amazon has the most aggressive bot detection (CAPTCHA, behavioral analysis, device
fingerprinting). Stealth mode helps but may not be sufficient. We use maximum human-like
behavior to maximize our chances.

NOTE: If stealth consistently fails, Amazon may require a different approach entirely
(e.g., Amazon Product Advertising API, or manual screenshot capture).
"""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Bestsellers in laptops category — less protected than search results
AMAZON_LAPTOPS_URL = "https://www.amazon.ca/gp/bestsellers/electronics/677252011"


class AmazonScraper(BaseScraper):
    retailer_slug = "amazon"
    retailer_name = "Amazon"
    stealth_enabled = True  # Required — aggressive bot detection without stealth

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Amazon's laptop bestsellers with maximum human-like behavior."""
        # Extensive pre-navigation behavior to appear human
        if self._use_stealth:
            await self.random_mouse_movement(page)
            await self.random_delay(2, 5)

        response = await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)

        # Check for CAPTCHA / robot check
        if await self.detect_access_denied(page, response):
            logger.warning(f"[{self.retailer_slug}] Amazon bot detection triggered")
            # Wait in case it's a soft challenge
            await asyncio.sleep(5)

        # Post-navigation human behavior
        if self._use_stealth:
            await self.random_delay(3, 7)
            await self.random_mouse_movement(page)

        try:
            await page.wait_for_selector(
                "#zg-ordered-list, .a-list-item, .p13n-desktop-grid", timeout=15_000
            )
        except Exception:
            logger.info(f"[{self.retailer_slug}] Bestseller grid not found, continuing with page as-is")

    async def dismiss_popups(self, page: Page) -> None:
        """Handle Amazon cookie consent and sign-in prompts."""
        try:
            consent = page.locator("#sp-cc-accept, button:has-text('Accept')")
            if await consent.first.is_visible(timeout=3000):
                await consent.first.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        try:
            dismiss = page.locator("#auth-pv-begin-no, a:has-text('No thanks')")
            if await dismiss.first.is_visible(timeout=2000):
                await dismiss.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def scroll_for_content(self, page: Page) -> None:
        """Scroll with extra human-like delays for Amazon."""
        await super().scroll_for_content(page)
        if self._use_stealth:
            await self.random_delay(2, 4)
            await self.random_mouse_movement(page)
