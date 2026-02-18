"""Integration tests for scraping API endpoints."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


# ── POST /api/scrape/run ──

class TestTriggerScrape:
    def test_trigger_scrape_all(self, client):
        """POST /api/scrape/run with retailer=all queues a background task."""
        with patch("api.scraping._background_scrape", new_callable=AsyncMock):
            res = client.post("/api/scrape/run", json={"retailer": "all", "trigger_type": "manual"})
        assert res.status_code == 200
        data = res.json()
        assert data["retailer"] == "all"
        assert data["trigger_type"] == "manual"
        assert "queued" in data["message"].lower() or "scrape" in data["message"].lower()

    def test_trigger_scrape_single_retailer(self, client):
        """POST /api/scrape/run for a specific valid retailer."""
        with patch("api.scraping._background_scrape", new_callable=AsyncMock):
            res = client.post("/api/scrape/run", json={"retailer": "bestbuy", "trigger_type": "manual"})
        assert res.status_code == 200
        assert res.json()["retailer"] == "bestbuy"

    def test_trigger_scrape_unknown_retailer(self, client):
        """POST /api/scrape/run with unknown retailer returns 400."""
        res = client.post("/api/scrape/run", json={"retailer": "fakeshop", "trigger_type": "manual"})
        assert res.status_code == 400
        assert "fakeshop" in res.json()["detail"]

    def test_trigger_scrape_disabled_retailer(self, client):
        """POST /api/scrape/run with disabled retailer returns 400."""
        res = client.post("/api/scrape/run", json={"retailer": "costco", "trigger_type": "manual"})
        assert res.status_code == 400
        assert "disabled" in res.json()["detail"].lower()

    def test_trigger_scrape_invalid_trigger_type(self, client):
        """POST /api/scrape/run with bad trigger_type returns 400."""
        res = client.post("/api/scrape/run", json={"retailer": "all", "trigger_type": "auto"})
        assert res.status_code == 400

    def test_trigger_scrape_while_running(self, client):
        """POST /api/scrape/run while scrape is running returns 409."""
        with patch("api.scraping.claim_scrape_lock", return_value=False):
            res = client.post("/api/scrape/run", json={"retailer": "all", "trigger_type": "manual"})
        assert res.status_code == 409
        assert "already" in res.json()["detail"].lower()

    def test_lock_released_after_empty_retailers(self, client, db_session):
        """Lock must be released when run_scrape returns early (no enabled retailers)."""
        from scrapers.manager import get_scrape_status, claim_scrape_lock, release_scrape_lock
        from database.models import Retailer

        # Disable all retailers
        db_session.query(Retailer).update({"scrape_enabled": False})
        db_session.commit()

        try:
            # Trigger scrape — background task will find no enabled retailers
            with patch("api.scraping._background_scrape", new_callable=AsyncMock) as mock_bg:
                res = client.post("/api/scrape/run", json={"retailer": "all", "trigger_type": "manual"})
            assert res.status_code == 200

            # Directly call run_scrape to simulate what the background task does
            import asyncio
            from scrapers.manager import run_scrape
            from database.models import SessionLocal
            db2 = SessionLocal()
            try:
                result = asyncio.get_event_loop().run_until_complete(run_scrape("all", "manual", db2))
                assert result == []
            finally:
                db2.close()

            # Lock MUST be released after empty-retailers early return
            status = get_scrape_status()
            assert status["running"] is False, "Lock was not released after empty retailers!"
        finally:
            # Re-enable retailers for other tests
            db_session.query(Retailer).filter(Retailer.slug.in_(["bestbuy", "staples", "walmart"])).update(
                {"scrape_enabled": True}, synchronize_session="fetch"
            )
            db_session.commit()


# ── GET /api/scrape/status ──

class TestScrapeStatus:
    def test_status_idle(self, client):
        """GET /api/scrape/status returns idle when nothing running."""
        res = client.get("/api/scrape/status")
        assert res.status_code == 200
        data = res.json()
        assert data["running"] is False

    def test_status_running(self, client):
        """GET /api/scrape/status returns running state with progress."""
        mock_status = {"running": True, "current_retailer": "walmart", "progress": 0.5, "retailers_completed": 2, "retailers_total": 4}
        with patch("api.scraping.get_scrape_status", return_value=mock_status):
            res = client.get("/api/scrape/status")
        assert res.status_code == 200
        data = res.json()
        assert data["running"] is True
        assert data["current_retailer"] == "walmart"
        assert data["progress"] == 0.5


# ── GET /api/scrape/runs ──

class TestListScrapeRuns:
    def test_list_empty(self, client):
        """GET /api/scrape/runs returns empty list when no runs exist."""
        res = client.get("/api/scrape/runs")
        assert res.status_code == 200
        data = res.json()
        assert "runs" in data
        assert isinstance(data["runs"], list)
        assert "total" in data

    def test_list_with_runs(self, client, db_session):
        """GET /api/scrape/runs returns existing runs."""
        from database.models import ScrapeRun
        run = ScrapeRun(
            retailer="Best Buy",
            status="completed",
            trigger_type="manual",
            items_found=5,
            completed_at=datetime.now(timezone.utc),
        )
        db_session.add(run)
        db_session.commit()

        res = client.get("/api/scrape/runs")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        found = [r for r in data["runs"] if r["retailer"] == "Best Buy"]
        assert len(found) >= 1
        assert found[0]["status"] == "completed"
        assert found[0]["items_found"] == 5

    def test_list_filter_by_retailer(self, client, db_session):
        """GET /api/scrape/runs?retailer=Best Buy filters correctly."""
        from database.models import ScrapeRun
        db_session.add(ScrapeRun(retailer="Staples", status="completed", trigger_type="manual"))
        db_session.commit()

        res = client.get("/api/scrape/runs", params={"retailer": "Staples"})
        assert res.status_code == 200
        for run in res.json()["runs"]:
            assert run["retailer"] == "Staples"

    def test_list_filter_by_status(self, client, db_session):
        """GET /api/scrape/runs?status=failed filters correctly."""
        from database.models import ScrapeRun
        db_session.add(ScrapeRun(retailer="Walmart", status="failed", trigger_type="manual", error_message="timeout"))
        db_session.commit()

        res = client.get("/api/scrape/runs", params={"status": "failed"})
        assert res.status_code == 200
        for run in res.json()["runs"]:
            assert run["status"] == "failed"

    def test_list_invalid_status(self, client):
        """GET /api/scrape/runs?status=invalid returns 400."""
        res = client.get("/api/scrape/runs", params={"status": "invalid"})
        assert res.status_code == 400

    def test_list_pagination(self, client, db_session):
        """GET /api/scrape/runs with limit and offset paginates."""
        res = client.get("/api/scrape/runs", params={"limit": 2, "offset": 0})
        assert res.status_code == 200
        assert res.json()["limit"] == 2
        assert res.json()["offset"] == 0


# ── GET /api/scrape/runs/{id} ──

class TestGetScrapeRun:
    def test_get_existing_run(self, client, db_session):
        """GET /api/scrape/runs/{id} returns run details."""
        from database.models import ScrapeRun
        run = ScrapeRun(retailer="Best Buy", status="completed", trigger_type="scheduled", items_found=10)
        db_session.add(run)
        db_session.commit()
        db_session.refresh(run)

        res = client.get(f"/api/scrape/runs/{run.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == run.id
        assert data["retailer"] == "Best Buy"
        assert data["trigger_type"] == "scheduled"

    def test_get_nonexistent_run(self, client):
        """GET /api/scrape/runs/99999 returns 404."""
        res = client.get("/api/scrape/runs/99999")
        assert res.status_code == 404


# ── GET /api/screenshots ──

class TestScreenshots:
    def test_list_empty_for_unknown_retailer(self, client):
        """GET /api/screenshots?retailer=nonexistent returns empty list."""
        res = client.get("/api/screenshots", params={"retailer": "nonexistent_retailer"})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0
        assert data["screenshots"] == []

    def test_list_with_screenshots(self, client, screenshots_dir):
        """GET /api/screenshots lists saved screenshots."""
        # Create a test screenshot file
        retailer_dir = screenshots_dir / "bestbuy" / "2026-02-12"
        retailer_dir.mkdir(parents=True, exist_ok=True)
        test_png = retailer_dir / "120000_screenshot.png"
        test_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        res = client.get("/api/screenshots")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        found = [s for s in data["screenshots"] if s["retailer"] == "bestbuy"]
        assert len(found) >= 1
        assert found[0]["date"] == "2026-02-12"

    def test_filter_by_retailer(self, client, screenshots_dir):
        """GET /api/screenshots?retailer=bestbuy filters by retailer."""
        res = client.get("/api/screenshots", params={"retailer": "bestbuy"})
        assert res.status_code == 200
        for s in res.json()["screenshots"]:
            assert s["retailer"] == "bestbuy"

    def test_filter_by_date(self, client, screenshots_dir):
        """GET /api/screenshots?date=2026-02-12 filters by date."""
        res = client.get("/api/screenshots", params={"date": "2026-02-12"})
        assert res.status_code == 200
        for s in res.json()["screenshots"]:
            assert s["date"] == "2026-02-12"


# ── GET /api/screenshots/{retailer}/{date}/{filename} ──

class TestServeScreenshot:
    def test_serve_existing(self, client, screenshots_dir):
        """GET /api/screenshots/bestbuy/2026-02-12/test.png serves the file."""
        retailer_dir = screenshots_dir / "bestbuy" / "2026-02-12"
        retailer_dir.mkdir(parents=True, exist_ok=True)
        test_file = retailer_dir / "test.png"
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        test_file.write_bytes(png_data)

        res = client.get("/api/screenshots/bestbuy/2026-02-12/test.png")
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/png"
        assert len(res.content) == len(png_data)

    def test_serve_nonexistent(self, client):
        """GET /api/screenshots/fake/2026-01-01/nope.png returns 404."""
        res = client.get("/api/screenshots/fake/2026-01-01/nope.png")
        assert res.status_code == 404

    def test_path_traversal_blocked(self, client):
        """Path traversal attempts in screenshot paths are blocked."""
        res = client.get("/api/screenshots/../../../etc/passwd/2026-01-01/test.png")
        assert res.status_code in (404, 422)

    def test_screenshot_cache_headers(self, client, screenshots_dir):
        """Screenshot responses include cache headers."""
        retailer_dir = screenshots_dir / "bestbuy" / "2026-02-12"
        retailer_dir.mkdir(parents=True, exist_ok=True)
        (retailer_dir / "cached.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)

        res = client.get("/api/screenshots/bestbuy/2026-02-12/cached.png")
        assert res.status_code == 200
        assert "max-age" in res.headers.get("cache-control", "")


# ── GET /api/retailers ──

class TestRetailers:
    def test_list_retailers(self, client):
        """GET /api/retailers returns all seeded retailers."""
        res = client.get("/api/retailers")
        assert res.status_code == 200
        data = res.json()
        assert "retailers" in data
        slugs = [r["slug"] for r in data["retailers"]]
        assert "bestbuy" in slugs
        assert "staples" in slugs

    def test_retailer_fields(self, client):
        """Each retailer has expected fields."""
        res = client.get("/api/retailers")
        for r in res.json()["retailers"]:
            assert "id" in r
            assert "name" in r
            assert "slug" in r
            assert "base_url" in r
            assert "scrape_enabled" in r
            assert "last_scraped" in r

    def test_disabled_retailer_visible(self, client):
        """Disabled retailers still appear in the list."""
        res = client.get("/api/retailers")
        costco = [r for r in res.json()["retailers"] if r["slug"] == "costco"]
        assert len(costco) == 1
        assert costco[0]["scrape_enabled"] is False


# ── GET /api/health ──

class TestHealth:
    def test_health_endpoint(self, client):
        """GET /api/health returns ok with v0.2.0."""
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.2.0"
