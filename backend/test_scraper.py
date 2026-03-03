import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO)

from scrapers.retailers import SCRAPER_REGISTRY

async def test_scraper(slug, url):
    scraper_class = SCRAPER_REGISTRY.get(slug)
    if not scraper_class:
        print(f"No scraper for {slug}")
        return
    scraper = scraper_class(base_url=url)
    print(f"Testing {slug} at {url}...")
    result = await scraper.run()
    print(f"  Status: {result.status}")
    print(f"  Title: {result.page_title}")
    print(f"  URL: {result.page_url}")
    print(f"  Error: {result.error_message}")
    print(f"  Screenshot: {len(result.screenshot_bytes) if result.screenshot_bytes else 0} bytes")
    print(f"  HTML: {len(result.html_content) if result.html_content else 0} chars")
    if result.screenshot_bytes:
        path = f"/home/node/.openclaw/workspace/ecom-watch/test_{slug}.png"
        with open(path, "wb") as f:
            f.write(result.screenshot_bytes)
        print(f"  Saved: {path}")
    return result

if __name__ == "__main__":
    slug = sys.argv[1]
    url = sys.argv[2] if len(sys.argv) > 2 else None
    if not url:
        from database.models import SessionLocal, Retailer
        db = SessionLocal()
        r = db.query(Retailer).filter(Retailer.slug == slug).first()
        if r: url = r.base_url
        db.close()
    asyncio.run(test_scraper(slug, url))
