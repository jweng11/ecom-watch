"""Amazon Canada scraper — amazon.ca laptop bestsellers and deals."""

import asyncio
import logging

from playwright.async_api import Page

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    retailer_slug = "amazon"
    retailer_name = "Amazon"

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to Amazon's laptop bestsellers page."""
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)
        try:
            await page.wait_for_selector("#zg-ordered-list, .a-list-item, .p13n-desktop-grid", timeout=15_000)
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

        # "Sign in for best experience" dismiss
        try:
            dismiss = page.locator("#auth-pv-begin-no, a:has-text('No thanks')")
            if await dismiss.first.is_visible(timeout=2000):
                await dismiss.first.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    # scroll_for_content: uses BaseScraper default (scrolls + iteration cap)
