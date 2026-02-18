"""Base scraper class providing Playwright browser automation, screenshot capture, and error handling."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

USER_AGENT = "Ecom-Watch/0.2.0 (Laptop price monitoring for internal competitive analysis)"
NAV_TIMEOUT_MS = 30_000
PAGE_LOAD_TIMEOUT_MS = 60_000
RATE_LIMIT_SECONDS = 5
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]
MAX_SCROLL_ITERATIONS = 50


@dataclass
class ScrapeResult:
    """Result of a single retailer scrape operation."""
    status: str = "completed"             # completed / failed / partial
    screenshot_paths: list[str] = field(default_factory=list)
    html_path: Optional[str] = None
    page_title: Optional[str] = None
    page_url: Optional[str] = None
    items_found: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Raw captured data — used by the manager to save via storage utils
    screenshot_bytes: Optional[bytes] = None
    html_content: Optional[str] = None


class BaseScraper:
    """
    Template-method base class for retailer scrapers.

    Subclasses must define:
        retailer_slug: str  — matches the Retailer.slug in the database
        retailer_name: str  — display name

    Subclasses should override:
        navigate_to_deals(page) — navigate to the retailer's deals/promotions page
        dismiss_popups(page)    — close cookie banners, modals, etc.
        scroll_for_content(page) — scroll to load lazy content
    """

    retailer_slug: str = ""
    retailer_name: str = ""

    def __init__(self, base_url: str, scrape_config: Optional[dict] = None):
        self.base_url = base_url
        self.scrape_config = scrape_config or {}
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None

    async def _launch_browser(self) -> BrowserContext:
        """Launch headless Chromium and return a browser context."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self._context = await self._browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            locale="en-CA",
            timezone_id="America/Toronto",
        )
        self._context.set_default_timeout(NAV_TIMEOUT_MS)
        return self._context

    async def _close_browser(self):
        """Clean up browser resources."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.warning(f"[{self.retailer_slug}] Browser cleanup error: {e}")
        finally:
            self._context = None
            self._browser = None
            self._playwright = None

    async def navigate_to_deals(self, page: Page) -> None:
        """
        Navigate to the retailer's deals page. Override in subclasses for
        site-specific navigation (clicking filters, selecting categories, etc.).
        Default implementation navigates to base_url.
        """
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)

    async def dismiss_popups(self, page: Page) -> None:
        """
        Dismiss cookie banners, newsletter popups, etc. Override in subclasses.
        Default implementation attempts common dismiss patterns.
        """
        common_selectors = [
            "button:has-text('Accept')",
            "button:has-text('Accept All')",
            "button:has-text('I Accept')",
            "button:has-text('Got it')",
            "button:has-text('Close')",
            "[aria-label='Close']",
            ".cookie-banner button",
            "#onetrust-accept-btn-handler",
        ]
        for selector in common_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=1000):
                    await btn.click()
                    await asyncio.sleep(0.5)
                    break
            except Exception:
                continue

    async def scroll_for_content(self, page: Page) -> None:
        """
        Scroll to trigger lazy loading. Override for sites that need special scrolling.
        Default scrolls down in increments, with a safety cap to prevent infinite loops.
        """
        viewport_height = page.viewport_size["height"]
        page_height = await page.evaluate("() => document.body.scrollHeight")
        position = 0
        iterations = 0
        while position < page_height and iterations < MAX_SCROLL_ITERATIONS:
            position += viewport_height * 0.8
            await page.evaluate(f"window.scrollTo(0, {int(position)})")
            await asyncio.sleep(0.5)
            # Check if new content loaded (page got taller)
            new_height = await page.evaluate("() => document.body.scrollHeight")
            if new_height > page_height:
                page_height = new_height
            iterations += 1
        if iterations >= MAX_SCROLL_ITERATIONS:
            logger.warning(f"[{self.retailer_slug}] Scroll capped at {MAX_SCROLL_ITERATIONS} iterations")

    async def capture_screenshot(self, page: Page) -> bytes:
        """Capture a full-page screenshot as PNG bytes."""
        return await page.screenshot(full_page=True, type="png")

    async def capture_html(self, page: Page) -> str:
        """Capture the full page HTML content."""
        return await page.content()

    async def run(self) -> ScrapeResult:
        """
        Execute the full scrape flow with retries and error handling.

        Flow: launch browser → navigate → dismiss popups → scroll → screenshot → save HTML → cleanup
        """
        result = ScrapeResult(started_at=datetime.now(timezone.utc))
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    wait_time = RETRY_BACKOFF[min(attempt - 1, len(RETRY_BACKOFF) - 1)]
                    logger.info(f"[{self.retailer_slug}] Retry {attempt}/{MAX_RETRIES} after {wait_time}s")
                    await asyncio.sleep(wait_time)

                context = await self._launch_browser()
                page = await context.new_page()

                # Navigate to deals page
                logger.info(f"[{self.retailer_slug}] Navigating to {self.base_url}")
                await self.navigate_to_deals(page)
                await asyncio.sleep(RATE_LIMIT_SECONDS)

                # Handle popups
                await self.dismiss_popups(page)

                # Scroll to load lazy content
                await self.scroll_for_content(page)
                await asyncio.sleep(1)  # Let content settle

                # Capture screenshot
                screenshot_bytes = await self.capture_screenshot(page)

                # Capture HTML for Phase 3 AI extraction
                html_content = await self.capture_html(page)

                result.page_title = await page.title()
                result.page_url = page.url
                result.status = "completed"
                result.completed_at = datetime.now(timezone.utc)

                # Store captured data for the manager to save via storage utils
                result.screenshot_bytes = screenshot_bytes
                result.html_content = html_content

                logger.info(f"[{self.retailer_slug}] Scrape completed successfully")
                return result

            except PlaywrightTimeout as e:
                last_error = f"Timeout: {e}"
                logger.warning(f"[{self.retailer_slug}] Attempt {attempt + 1} timed out: {e}")
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(f"[{self.retailer_slug}] Attempt {attempt + 1} failed: {e}")
            finally:
                await self._close_browser()

        # All retries exhausted
        result.status = "failed"
        result.error_message = last_error
        result.completed_at = datetime.now(timezone.utc)
        logger.error(f"[{self.retailer_slug}] All {MAX_RETRIES} attempts failed: {last_error}")
        return result
