"""Tests for screenshot/HTML storage utilities."""

import os
import sys
from datetime import date
from pathlib import Path

import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


class TestSaveScreenshot:
    def test_saves_png_file(self, screenshots_dir):
        """save_screenshot creates a PNG file in the correct directory."""
        from scrapers.utils.storage import save_screenshot
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
        rel_path = save_screenshot("bestbuy", png_data, scrape_date=date(2026, 2, 12))

        full_path = screenshots_dir / rel_path
        assert full_path.exists()
        assert full_path.read_bytes() == png_data
        assert "bestbuy" in rel_path
        assert "2026-02-12" in rel_path
        assert rel_path.endswith(".png")

    def test_creates_directory_structure(self, screenshots_dir):
        """save_screenshot creates retailer/date subdirectories."""
        from scrapers.utils.storage import save_screenshot
        save_screenshot("newretailer", b"\x89PNG" + b"\x00" * 10, scrape_date=date(2026, 3, 15))
        assert (screenshots_dir / "newretailer" / "2026-03-15").is_dir()


class TestSaveHtml:
    def test_saves_html_file(self, screenshots_dir):
        """save_html creates an HTML file in the correct directory."""
        from scrapers.utils.storage import save_html
        html = "<html><body>Test page</body></html>"
        rel_path = save_html("staples", html, scrape_date=date(2026, 2, 12))

        full_path = screenshots_dir / rel_path
        assert full_path.exists()
        assert full_path.read_text(encoding="utf-8") == html
        assert rel_path.endswith(".html")


class TestSaveMetadata:
    def test_saves_json_metadata(self, screenshots_dir):
        """save_metadata creates a JSON file with the provided data."""
        from scrapers.utils.storage import save_metadata
        import json
        metadata = {"scrape_run_id": 1, "retailer": "Walmart", "status": "completed"}
        rel_path = save_metadata("walmart", metadata, scrape_date=date(2026, 2, 12))

        full_path = screenshots_dir / rel_path
        assert full_path.exists()
        loaded = json.loads(full_path.read_text())
        assert loaded["retailer"] == "Walmart"
        assert loaded["status"] == "completed"


class TestListScreenshots:
    def test_list_all(self, screenshots_dir):
        """list_screenshots returns all screenshots across retailers."""
        from scrapers.utils.storage import list_screenshots, save_screenshot
        save_screenshot("bestbuy", b"\x89PNG" + b"\x00" * 10, scrape_date=date(2026, 1, 1))
        save_screenshot("staples", b"\x89PNG" + b"\x00" * 10, scrape_date=date(2026, 1, 2))

        results = list_screenshots()
        retailers = {s["retailer"] for s in results}
        assert "bestbuy" in retailers
        assert "staples" in retailers

    def test_filter_by_retailer(self, screenshots_dir):
        """list_screenshots filters by retailer slug."""
        from scrapers.utils.storage import list_screenshots, save_screenshot
        save_screenshot("walmart", b"\x89PNG" + b"\x00" * 10, scrape_date=date(2026, 1, 5))

        results = list_screenshots(retailer_slug="walmart")
        for s in results:
            assert s["retailer"] == "walmart"

    def test_filter_by_date(self, screenshots_dir):
        """list_screenshots filters by date string."""
        from scrapers.utils.storage import list_screenshots, save_screenshot
        save_screenshot("bestbuy", b"\x89PNG" + b"\x00" * 10, scrape_date=date(2026, 6, 15))

        results = list_screenshots(retailer_slug="bestbuy", scrape_date="2026-06-15")
        for s in results:
            assert s["date"] == "2026-06-15"

    def test_includes_file_size(self, screenshots_dir):
        """list_screenshots includes file size in bytes."""
        from scrapers.utils.storage import list_screenshots, save_screenshot
        png_data = b"\x89PNG" + b"\x00" * 500
        save_screenshot("costco", png_data, scrape_date=date(2026, 7, 1))

        results = list_screenshots(retailer_slug="costco", scrape_date="2026-07-01")
        assert len(results) >= 1
        assert results[0]["size_bytes"] == len(png_data)

    def test_empty_when_no_files(self, screenshots_dir):
        """list_screenshots returns empty list for nonexistent retailer."""
        from scrapers.utils.storage import list_screenshots
        results = list_screenshots(retailer_slug="nonexistent")
        assert results == []

    def test_blocks_path_traversal_in_retailer(self, screenshots_dir):
        """list_screenshots blocks path traversal in retailer_slug."""
        from scrapers.utils.storage import list_screenshots
        results = list_screenshots(retailer_slug="../etc")
        assert results == []

    def test_blocks_path_traversal_in_date(self, screenshots_dir):
        """list_screenshots blocks path traversal in scrape_date."""
        from scrapers.utils.storage import list_screenshots
        results = list_screenshots(retailer_slug="bestbuy", scrape_date="../../etc")
        assert results == []


class TestGetScreenshotFilepath:
    def test_resolves_existing_file(self, screenshots_dir):
        """get_screenshot_filepath returns Path for existing files."""
        from scrapers.utils.storage import get_screenshot_filepath
        target_dir = screenshots_dir / "bestbuy" / "2026-02-12"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "test.png").write_bytes(b"\x89PNG" + b"\x00" * 10)

        result = get_screenshot_filepath("bestbuy", "2026-02-12", "test.png")
        assert result is not None
        assert result.exists()

    def test_returns_none_for_missing(self, screenshots_dir):
        """get_screenshot_filepath returns None for missing files."""
        from scrapers.utils.storage import get_screenshot_filepath
        result = get_screenshot_filepath("bestbuy", "2099-01-01", "missing.png")
        assert result is None

    def test_blocks_path_traversal(self, screenshots_dir):
        """get_screenshot_filepath blocks .. in path components."""
        from scrapers.utils.storage import get_screenshot_filepath
        result = get_screenshot_filepath("../etc", "passwd", "shadow")
        assert result is None

    def test_blocks_slashes(self, screenshots_dir):
        """get_screenshot_filepath blocks slashes in components."""
        from scrapers.utils.storage import get_screenshot_filepath
        result = get_screenshot_filepath("bestbuy/../../etc", "2026-01-01", "test.png")
        assert result is None
