"""Base scraper class providing Playwright browser automation, screenshot capture, and error handling.

Includes optional stealth mode with anti-detection measures, human-like behavior simulation,
Cloudflare challenge detection, and escalating retry strategies.
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Response,
    TimeoutError as PlaywrightTimeout,
)

logger = logging.getLogger(__name__)

# Legacy UA kept for backward-compat reference; stealth mode overrides this
USER_AGENT = "Ecom-Watch/0.2.0 (Laptop price monitoring for internal competitive analysis)"
NAV_TIMEOUT_MS = 30_000
PAGE_LOAD_TIMEOUT_MS = 60_000
RATE_LIMIT_SECONDS = 5
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]
MAX_SCROLL_ITERATIONS = 50

# Stealth defaults (overridden by config.py values when available)
_DEFAULT_STEALTH_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]
_DEFAULT_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1366, "height": 768},
]


def _load_stealth_config():
    """Load stealth settings from config.py, falling back to defaults."""
    try:
        from config import (
            STEALTH_ENABLED,
            STEALTH_USER_AGENTS,
            STEALTH_VIEWPORTS,
            SCRAPE_MIN_DELAY,
            SCRAPE_MAX_DELAY,
        )
        return STEALTH_ENABLED, STEALTH_USER_AGENTS, STEALTH_VIEWPORTS, SCRAPE_MIN_DELAY, SCRAPE_MAX_DELAY
    except ImportError:
        return True, _DEFAULT_STEALTH_UAS, _DEFAULT_VIEWPORTS, 3, 8


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

    Stealth mode (enabled by default) adds anti-detection measures including
    randomized viewports/UAs, playwright-stealth patches, and human-like delays.
    Set `stealth_enabled = False` on subclass to disable.
    """

    retailer_slug: str = ""
    retailer_name: str = ""
    stealth_enabled: bool = True  # per-scraper opt-out; config.py can also disable globally

    def __init__(self, base_url: str, scrape_config: Optional[dict] = None):
        self.base_url = base_url
        self.scrape_config = scrape_config or {}
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None

    @property
    def _use_stealth(self) -> bool:
        """Whether stealth mode is active (both global config and per-scraper)."""
        global_enabled, *_ = _load_stealth_config()
        return global_enabled and self.stealth_enabled

    async def _launch_browser(self, ua_override: Optional[str] = None) -> BrowserContext:
        """Launch headless Chromium and return a browser context.

        When stealth mode is active:
        - Randomized viewport and User-Agent
        - Anti-automation browser args
        - playwright-stealth patches applied to context
        """
        _, user_agents, viewports, _, _ = _load_stealth_config()

        self._playwright = await async_playwright().start()

        launch_args = ["--no-sandbox", "--disable-dev-shm-usage"]

        if self._use_stealth:
            launch_args.extend([
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--window-position=0,0",
            ])

        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=launch_args,
        )

        if self._use_stealth:
            viewport = random.choice(viewports)
            ua = ua_override or random.choice(user_agents)
        else:
            viewport = {"width": 1920, "height": 1080}
            ua = USER_AGENT

        self._context = await self._browser.new_context(
            user_agent=ua,
            viewport=viewport,
            locale="en-CA",
            timezone_id="America/Toronto",
        )
        self._context.set_default_timeout(NAV_TIMEOUT_MS)

        # Apply playwright-stealth patches
        if self._use_stealth:
            try:
                from playwright_stealth import stealth_async
                await stealth_async(self._context)
                logger.debug(f"[{self.retailer_slug}] Stealth patches applied")
            except ImportError:
                logger.warning(f"[{self.retailer_slug}] playwright-stealth not installed, skipping stealth patches")

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

    # --- Human-like behavior methods ---

    async def random_delay(self, min_s: float = 1.0, max_s: float = 3.0) -> None:
        """Sleep for a random duration to mimic human timing."""
        delay = random.uniform(min_s, max_s)
        await asyncio.sleep(delay)

    async def human_scroll(self, page: Page) -> None:
        """Scroll the page with variable speed, random pauses, and occasional scroll-up."""
        viewport_height = page.viewport_size["height"]
        page_height = await page.evaluate("() => document.body.scrollHeight")
        position = 0
        iterations = 0

        while position < page_height and iterations < MAX_SCROLL_ITERATIONS:
            # Variable scroll distance (60-100% of viewport)
            scroll_amount = int(viewport_height * random.uniform(0.6, 1.0))
            position += scroll_amount
            await page.evaluate(f"window.scrollTo(0, {int(position)})")
            await asyncio.sleep(random.uniform(0.3, 1.2))

            # Occasional scroll-up to appear human (~15% chance)
            if random.random() < 0.15 and position > viewport_height:
                scroll_back = int(viewport_height * random.uniform(0.2, 0.5))
                position -= scroll_back
                await page.evaluate(f"window.scrollTo(0, {int(position)})")
                await asyncio.sleep(random.uniform(0.5, 1.0))

            # Check if new content loaded
            new_height = await page.evaluate("() => document.body.scrollHeight")
            if new_height > page_height:
                page_height = new_height
            iterations += 1

        if iterations >= MAX_SCROLL_ITERATIONS:
            logger.warning(f"[{self.retailer_slug}] Scroll capped at {MAX_SCROLL_ITERATIONS} iterations")

    async def random_mouse_movement(self, page: Page) -> None:
        """Move mouse to random positions to simulate human cursor activity."""
        viewport = page.viewport_size
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, viewport["width"] - 100)
            y = random.randint(100, viewport["height"] - 100)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.4))

    # --- Cloudflare / WAF detection ---

    async def detect_cloudflare_challenge(self, page: Page) -> bool:
        """Check if the page is showing a Cloudflare challenge."""
        title = await page.title()
        challenge_titles = ["Just a moment...", "Attention Required", "Access denied"]
        if any(t.lower() in title.lower() for t in challenge_titles):
            return True

        content = await page.content()
        challenge_markers = [
            "cf-browser-verification",
            "challenge-platform",
            "cf-challenge-running",
            "cf_chl_opt",
        ]
        return any(marker in content for marker in challenge_markers)

    async def wait_for_challenge_resolution(self, page: Page, timeout_s: float = 10.0) -> bool:
        """Wait for a Cloudflare/WAF challenge to auto-resolve.

        Returns True if the challenge resolved, False if still present after timeout.
        """
        logger.info(f"[{self.retailer_slug}] Challenge detected, waiting up to {timeout_s}s for resolution...")
        elapsed = 0.0
        interval = 1.0
        while elapsed < timeout_s:
            await asyncio.sleep(interval)
            elapsed += interval
            if not await self.detect_cloudflare_challenge(page):
                logger.info(f"[{self.retailer_slug}] Challenge resolved after {elapsed:.0f}s")
                return True
        logger.warning(f"[{self.retailer_slug}] Challenge did NOT resolve within {timeout_s}s")
        return False

    async def detect_access_denied(self, page: Page, response: Optional[Response] = None) -> bool:
        """Check for generic WAF blocks (Akamai, PerimeterX, etc.)."""
        if response and response.status in (403, 429, 503):
            return True
        title = (await page.title()).lower()
        blocked_titles = ["access denied", "robot check", "are you a robot", "blocked"]
        return any(t in title for t in blocked_titles)

    # --- Template methods (override in subclasses) ---

    async def navigate_to_deals(self, page: Page) -> None:
        """Navigate to the retailer's deals page. Override in subclasses."""
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)

    async def dismiss_popups(self, page: Page) -> None:
        """Dismiss cookie banners, newsletter popups, etc. Override in subclasses."""
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
        """Scroll to trigger lazy loading. Override for sites that need special scrolling."""
        if self._use_stealth:
            await self.human_scroll(page)
        else:
            # Original non-stealth scrolling
            viewport_height = page.viewport_size["height"]
            page_height = await page.evaluate("() => document.body.scrollHeight")
            position = 0
            iterations = 0
            while position < page_height and iterations < MAX_SCROLL_ITERATIONS:
                position += viewport_height * 0.8
                await page.evaluate(f"window.scrollTo(0, {int(position)})")
                await asyncio.sleep(0.5)
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

    async def _attempt_scrape(self, attempt: int) -> ScrapeResult:
        """Execute a single scrape attempt with escalating stealth measures."""
        _, user_agents, _, min_delay, max_delay = _load_stealth_config()
        result = ScrapeResult()

        # Escalation: attempt 1 = normal stealth, attempt 2 = different UA + longer delays
        ua_override = None
        if attempt >= 1 and self._use_stealth:
            ua_override = random.choice(user_agents)
            min_delay = min_delay * 1.5
            max_delay = max_delay * 1.5

        context = await self._launch_browser(ua_override=ua_override)
        page = await context.new_page()

        # Pre-navigation human behavior
        if self._use_stealth:
            await self.random_mouse_movement(page)

        # Navigate
        logger.info(f"[{self.retailer_slug}] Navigating to {self.base_url} (attempt {attempt + 1})")
        await self.navigate_to_deals(page)

        # Check for challenges/blocks
        if self._use_stealth:
            if await self.detect_cloudflare_challenge(page):
                resolved = await self.wait_for_challenge_resolution(page)
                if not resolved:
                    result.status = "blocked"
                    result.error_message = "Cloudflare challenge not resolved"
                    result.page_title = await page.title()
                    result.page_url = page.url
                    return result

            if await self.detect_access_denied(page):
                content_snippet = (await page.content())[:500]
                result.status = "blocked"
                result.error_message = f"Access denied. Title: {await page.title()}. Snippet: {content_snippet}"
                result.page_title = await page.title()
                result.page_url = page.url
                return result

        # Rate-limit delay
        if self._use_stealth:
            await self.random_delay(min_delay, max_delay)
        else:
            await asyncio.sleep(RATE_LIMIT_SECONDS)

        # Handle popups
        await self.dismiss_popups(page)

        # Scroll to load lazy content
        await self.scroll_for_content(page)
        await asyncio.sleep(1)

        # Post-scroll human behavior
        if self._use_stealth:
            await self.random_mouse_movement(page)

        # Capture
        result.screenshot_bytes = await self.capture_screenshot(page)
        result.html_content = await self.capture_html(page)
        result.page_title = await page.title()
        result.page_url = page.url
        result.status = "completed"
        return result

    async def run(self) -> ScrapeResult:
        """Execute the full scrape flow with retries and escalating stealth.

        Retry strategy:
          Attempt 1: headless with stealth
          Attempt 2: stealth + different UA + longer delays
          Attempt 3: log failure with diagnostic info
        """
        result = ScrapeResult(started_at=datetime.now(timezone.utc))
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    wait_time = RETRY_BACKOFF[min(attempt - 1, len(RETRY_BACKOFF) - 1)]
                    logger.info(f"[{self.retailer_slug}] Retry {attempt}/{MAX_RETRIES} after {wait_time}s")
                    await asyncio.sleep(wait_time)

                attempt_result = await self._attempt_scrape(attempt)

                if attempt_result.status == "completed":
                    result.screenshot_bytes = attempt_result.screenshot_bytes
                    result.html_content = attempt_result.html_content
                    result.page_title = attempt_result.page_title
                    result.page_url = attempt_result.page_url
                    result.status = "completed"
                    result.completed_at = datetime.now(timezone.utc)
                    logger.info(f"[{self.retailer_slug}] Scrape completed successfully")
                    return result

                if attempt_result.status == "blocked":
                    last_error = attempt_result.error_message
                    logger.warning(
                        f"[{self.retailer_slug}] Attempt {attempt + 1} blocked: {last_error}"
                    )
                    continue

            except PlaywrightTimeout as e:
                last_error = f"Timeout: {e}"
                logger.warning(f"[{self.retailer_slug}] Attempt {attempt + 1} timed out: {e}")
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(f"[{self.retailer_slug}] Attempt {attempt + 1} failed: {e}")
            finally:
                await self._close_browser()

        # All retries exhausted — log diagnostic info
        result.status = "failed"
        result.error_message = last_error
        result.completed_at = datetime.now(timezone.utc)
        logger.error(f"[{self.retailer_slug}] All {MAX_RETRIES} attempts failed: {last_error}")
        return result
