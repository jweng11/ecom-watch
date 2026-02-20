#!/usr/bin/env python3
"""Stealth scraping test — tests each retailer with stealth mode enabled.

Run on the Jetson (requires Playwright system deps):
    cd backend && python test_stealth.py

For each retailer, this script:
  1. Launches a stealth browser
  2. Navigates to the retailer's URL
  3. Reports: blocked or not, page title, HTTP status
  4. Saves a screenshot to work/data/stealth_test/
  5. Saves first 500 chars of page content for analysis
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import SCREENSHOTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Test output directory
TEST_OUTPUT_DIR = SCREENSHOTS_DIR.parent / "stealth_test"
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Retailer URLs to test
RETAILERS = {
    "bestbuy": {
        "name": "Best Buy",
        "url": "https://www.bestbuy.ca/en-ca/collection/top-deals-laptops/36582",
        "protection": "Akamai WAF",
    },
    "staples": {
        "name": "Staples",
        "url": "https://www.staples.ca/collections/laptops-90",
        "protection": "Cloudflare",
    },
    "walmart": {
        "name": "Walmart",
        "url": "https://www.walmart.ca/browse/electronics/laptops/10003/30622",
        "protection": "PerimeterX",
    },
    "memoryexpress": {
        "name": "Memory Express",
        "url": "https://www.memoryexpress.com/Category/LaptopsNotebooks",
        "protection": "Cloudflare",
    },
    "amazon": {
        "name": "Amazon",
        "url": "https://www.amazon.ca/gp/bestsellers/electronics/677252011",
        "protection": "CAPTCHA / bot detection",
    },
    "canadacomputers": {
        "name": "Canada Computers",
        "url": "https://www.canadacomputers.com/promotions",
        "protection": "None (should work)",
    },
    "thesource": {
        "name": "The Source",
        "url": "https://www.thesource.ca/en-ca/computers-tablets/laptops/c/scc-1-2",
        "protection": "Minimal",
    },
}


async def test_retailer(slug: str, info: dict) -> dict:
    """Test a single retailer with stealth scraping."""
    from scrapers.base import BaseScraper

    result = {
        "slug": slug,
        "name": info["name"],
        "protection": info["protection"],
        "url": info["url"],
        "status": "unknown",
        "page_title": None,
        "blocked": None,
        "content_snippet": None,
        "error": None,
    }

    scraper = BaseScraper(base_url=info["url"])
    scraper.retailer_slug = slug
    scraper.retailer_name = info["name"]

    try:
        context = await scraper._launch_browser()
        page = await context.new_page()

        # Navigate
        response = await page.goto(info["url"], wait_until="domcontentloaded", timeout=60_000)
        http_status = response.status if response else "N/A"

        # Wait for any challenges
        is_cf = await scraper.detect_cloudflare_challenge(page)
        if is_cf:
            logger.info(f"[{slug}] Cloudflare challenge detected, waiting...")
            resolved = await scraper.wait_for_challenge_resolution(page, timeout_s=15)
            result["blocked"] = not resolved
        else:
            is_denied = await scraper.detect_access_denied(page, response)
            result["blocked"] = is_denied

        result["page_title"] = await page.title()
        result["status"] = f"HTTP {http_status}"

        # Content snippet
        content = await page.content()
        result["content_snippet"] = content[:500]

        # Screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = TEST_OUTPUT_DIR / f"{slug}_{timestamp}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"[{slug}] Screenshot saved: {screenshot_path}")

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        result["blocked"] = True
        logger.error(f"[{slug}] Test failed: {e}")
    finally:
        await scraper._close_browser()

    return result


async def main():
    """Run stealth tests on all retailers and print a summary."""
    print("=" * 70)
    print("STEALTH SCRAPING TEST")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Output dir: {TEST_OUTPUT_DIR}")
    print("=" * 70)

    results = []
    for slug, info in RETAILERS.items():
        print(f"\n{'─' * 50}")
        print(f"Testing: {info['name']} ({slug})")
        print(f"URL: {info['url']}")
        print(f"Protection: {info['protection']}")
        print(f"{'─' * 50}")

        result = await test_retailer(slug, info)
        results.append(result)

        status_icon = "✅" if not result["blocked"] else "❌"
        print(f"  {status_icon} Status: {result['status']}")
        print(f"  Title: {result['page_title']}")
        print(f"  Blocked: {result['blocked']}")
        if result["error"]:
            print(f"  Error: {result['error']}")

        # Brief delay between retailers
        await asyncio.sleep(2)

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    passed = sum(1 for r in results if not r["blocked"])
    total = len(results)
    print(f"  Passed: {passed}/{total}")
    for r in results:
        icon = "✅" if not r["blocked"] else "❌"
        print(f"  {icon} {r['name']:20s} — {r['status']:10s} — {r['page_title'] or 'N/A'}")


if __name__ == "__main__":
    asyncio.run(main())
