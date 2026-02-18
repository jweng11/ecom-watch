"""Screenshot and HTML storage utilities for the scraping engine."""

import json
import logging
import uuid
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Optional

from config import SCREENSHOTS_DIR

logger = logging.getLogger(__name__)


def _ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_retailer_date_dir(retailer_slug: str, scrape_date: Optional[date] = None) -> Path:
    """Get the storage directory for a retailer on a given date."""
    if scrape_date is None:
        scrape_date = datetime.now(timezone.utc).date()
    return _ensure_dir(SCREENSHOTS_DIR / retailer_slug / scrape_date.isoformat())


def save_screenshot(retailer_slug: str, png_bytes: bytes, scrape_date: Optional[date] = None) -> str:
    """
    Save a PNG screenshot to the organized directory structure.

    Returns the relative path from SCREENSHOTS_DIR (for database storage).
    """
    target_dir = get_retailer_date_dir(retailer_slug, scrape_date)
    timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    filename = f"{timestamp}_{short_id}_screenshot.png"
    filepath = target_dir / filename
    filepath.write_bytes(png_bytes)
    logger.info(f"Screenshot saved: {filepath} ({len(png_bytes)} bytes)")
    return str(filepath.relative_to(SCREENSHOTS_DIR))


def save_html(retailer_slug: str, html_content: str, scrape_date: Optional[date] = None) -> str:
    """
    Save HTML page content alongside screenshots.

    Returns the relative path from SCREENSHOTS_DIR.
    """
    target_dir = get_retailer_date_dir(retailer_slug, scrape_date)
    timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    filename = f"{timestamp}_{short_id}_page.html"
    filepath = target_dir / filename
    filepath.write_text(html_content, encoding="utf-8")
    logger.info(f"HTML saved: {filepath} ({len(html_content)} chars)")
    return str(filepath.relative_to(SCREENSHOTS_DIR))


def save_metadata(retailer_slug: str, metadata: dict, scrape_date: Optional[date] = None) -> str:
    """Save JSON metadata for a scrape run."""
    target_dir = get_retailer_date_dir(retailer_slug, scrape_date)
    timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    filename = f"{timestamp}_{short_id}_metadata.json"
    filepath = target_dir / filename
    filepath.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    return str(filepath.relative_to(SCREENSHOTS_DIR))


def list_screenshots(retailer_slug: Optional[str] = None, scrape_date: Optional[str] = None) -> list[dict]:
    """
    List available screenshots with metadata.

    Args:
        retailer_slug: Filter by retailer (None = all retailers)
        scrape_date: Filter by date string "YYYY-MM-DD" (None = all dates)

    Returns:
        List of dicts with: retailer, date, filename, path, size_bytes
    """
    results = []

    # Validate inputs against path traversal
    if retailer_slug:
        if ".." in retailer_slug or "/" in retailer_slug or "\\" in retailer_slug:
            logger.warning(f"Path traversal attempt in list_screenshots: {retailer_slug}")
            return []
    if scrape_date:
        if ".." in scrape_date or "/" in scrape_date or "\\" in scrape_date:
            logger.warning(f"Path traversal attempt in list_screenshots date: {scrape_date}")
            return []

    if not SCREENSHOTS_DIR.exists():
        return []

    if retailer_slug:
        retailer_dirs = [SCREENSHOTS_DIR / retailer_slug]
    else:
        retailer_dirs = [d for d in SCREENSHOTS_DIR.iterdir() if d.is_dir()]

    for retailer_dir in retailer_dirs:
        if not retailer_dir.exists():
            continue
        slug = retailer_dir.name

        if scrape_date:
            date_dirs = [retailer_dir / scrape_date]
        else:
            date_dirs = sorted(
                [d for d in retailer_dir.iterdir() if d.is_dir()],
                reverse=True,
            )

        for date_dir in date_dirs:
            if not date_dir.exists():
                continue
            for png_file in sorted(date_dir.glob("*.png"), reverse=True):
                results.append({
                    "retailer": slug,
                    "date": date_dir.name,
                    "filename": png_file.name,
                    "path": f"{slug}/{date_dir.name}/{png_file.name}",
                    "size_bytes": png_file.stat().st_size,
                })

    return results


def get_screenshot_filepath(retailer: str, date_str: str, filename: str) -> Optional[Path]:
    """
    Resolve a screenshot path. Returns None if the file doesn't exist.
    Validates components to prevent path traversal.
    """
    # Sanitize inputs against path traversal
    for component in [retailer, date_str, filename]:
        if ".." in component or "/" in component or "\\" in component:
            logger.warning(f"Path traversal attempt blocked: {component}")
            return None

    filepath = SCREENSHOTS_DIR / retailer / date_str / filename
    if filepath.exists() and filepath.is_file():
        return filepath
    return None
