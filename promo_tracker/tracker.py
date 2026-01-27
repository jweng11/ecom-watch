#!/usr/bin/env python3
"""
Laptop Promotion Tracker
========================
Scrapes laptop deals from major retailers, takes screenshots,
and uses an LLM to extract and maintain structured data in Excel.

Usage:
    python tracker.py              # Run full scrape + analysis
    python tracker.py --scrape     # Only scrape (no LLM analysis)
    python tracker.py --analyze    # Only analyze existing screenshots
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import (
    SITES,
    OUTPUT_DIR,
    SCREENSHOTS_DIR,
    EXCEL_FILE,
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    BROWSER_VIEWPORT,
    PAGE_LOAD_WAIT_MS,
    REQUEST_TIMEOUT_MS,
    USER_AGENT,
)
from llm_analyzer import analyze_screenshot
from excel_manager import add_promotions, create_summary_sheet


def setup_directories():
    """Create output directories if they don't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


def get_api_key() -> str:
    """Get the API key for the configured LLM provider."""
    if LLM_PROVIDER == "anthropic":
        if not ANTHROPIC_API_KEY:
            print("Error: ANTHROPIC_API_KEY not set.")
            print("Set it via: export ANTHROPIC_API_KEY='your-key-here'")
            sys.exit(1)
        return ANTHROPIC_API_KEY
    elif LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            print("Error: OPENAI_API_KEY not set.")
            print("Set it via: export OPENAI_API_KEY='your-key-here'")
            sys.exit(1)
        return OPENAI_API_KEY
    else:
        print(f"Error: Unknown LLM_PROVIDER: {LLM_PROVIDER}")
        sys.exit(1)


def scrape_sites() -> list[dict]:
    """
    Scrape all configured sites and take screenshots.

    Returns:
        List of dicts with site info and screenshot paths
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    date_str = datetime.now().strftime("%Y-%m-%d")
    results = []

    print("\n" + "=" * 60)
    print("SCRAPING RETAILER SITES")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport=BROWSER_VIEWPORT,
            user_agent=USER_AGENT,
        )
        page = context.new_page()

        for site in SITES:
            print(f"\n[{site['retailer']}] {site['url']}")

            try:
                page.goto(site["url"], timeout=REQUEST_TIMEOUT_MS)
                page.wait_for_timeout(PAGE_LOAD_WAIT_MS)

                # Scroll down to load lazy content
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                page.wait_for_timeout(1000)

                # Take screenshot
                screenshot_filename = f"{site['name']}_{timestamp}.png"
                screenshot_path = SCREENSHOTS_DIR / screenshot_filename
                page.screenshot(path=str(screenshot_path), full_page=True)

                print(f"  Screenshot saved: {screenshot_filename}")

                results.append({
                    "site": site,
                    "screenshot_path": str(screenshot_path),
                    "timestamp": timestamp,
                    "date": date_str,
                    "success": True,
                })

            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({
                    "site": site,
                    "screenshot_path": None,
                    "timestamp": timestamp,
                    "date": date_str,
                    "success": False,
                    "error": str(e),
                })

        browser.close()

    successful = sum(1 for r in results if r["success"])
    print(f"\nScraped {successful}/{len(SITES)} sites successfully")

    return results


def analyze_and_save(scrape_results: list[dict], api_key: str):
    """
    Analyze screenshots with LLM and save to Excel.

    Args:
        scrape_results: Results from scrape_sites()
        api_key: API key for LLM provider
    """
    print("\n" + "=" * 60)
    print("ANALYZING WITH LLM")
    print("=" * 60)

    total_promotions = 0

    for result in scrape_results:
        if not result["success"]:
            print(f"\n[{result['site']['retailer']}] Skipped (scrape failed)")
            continue

        site = result["site"]
        print(f"\n[{site['retailer']}] Analyzing screenshot...")

        try:
            promotions = analyze_screenshot(
                image_path=result["screenshot_path"],
                retailer=site["retailer"],
                provider=LLM_PROVIDER,
                api_key=api_key,
            )

            if promotions:
                count = add_promotions(
                    filepath=EXCEL_FILE,
                    promotions=promotions,
                    scrape_date=result["date"],
                    retailer=site["retailer"],
                    screenshot_path=result["screenshot_path"],
                    source_url=site["url"],
                )
                print(f"  Found {count} promotions")
                total_promotions += count
            else:
                print("  No promotions found")

        except Exception as e:
            print(f"  ERROR analyzing: {e}")

    # Update summary sheet
    if total_promotions > 0:
        create_summary_sheet(EXCEL_FILE)
        print(f"\n Total promotions added: {total_promotions}")
        print(f"Excel file: {EXCEL_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="Laptop Promotion Tracker - Scrape, screenshot, and analyze deals"
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Only scrape sites (skip LLM analysis)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Only analyze most recent screenshots (skip scraping)"
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  LAPTOP PROMOTION TRACKER")
    print("=" * 60)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Provider: {LLM_PROVIDER}")
    print("=" * 60)

    setup_directories()

    # Determine what to do
    if args.analyze:
        # Find most recent screenshots
        api_key = get_api_key()
        print("\nAnalyzing most recent screenshots...")
        # Get latest timestamp
        screenshots = list(SCREENSHOTS_DIR.glob("*.png"))
        if not screenshots:
            print("No screenshots found to analyze")
            sys.exit(1)

        # Group by timestamp
        latest = max(screenshots, key=lambda p: p.stat().st_mtime)
        timestamp = "_".join(latest.stem.split("_")[-2:])

        results = []
        for site in SITES:
            screenshot_path = SCREENSHOTS_DIR / f"{site['name']}_{timestamp}.png"
            if screenshot_path.exists():
                results.append({
                    "site": site,
                    "screenshot_path": str(screenshot_path),
                    "timestamp": timestamp,
                    "date": timestamp.split("_")[0],
                    "success": True,
                })

        analyze_and_save(results, api_key)

    elif args.scrape:
        scrape_sites()
        print("\nScrape complete. Run without --scrape to analyze.")

    else:
        # Full run: scrape + analyze
        api_key = get_api_key()
        results = scrape_sites()
        analyze_and_save(results, api_key)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
