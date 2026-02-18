"""Shared test fixtures for Ecom-Watch backend tests."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend is on the path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Override the database to use a temporary SQLite file for all tests."""
    # Use local filesystem to avoid FUSE mount temp cleanup issues
    local_tmp = Path("/sessions/practical-youthful-faraday/test_tmp")
    local_tmp.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(dir=local_tmp))
    test_db = tmp_dir / "test.db"
    test_screenshots = tmp_dir / "screenshots"
    test_screenshots.mkdir()

    # Patch config before importing anything else
    import config
    config.DB_PATH = test_db
    config.DATABASE_URL = f"sqlite:///{test_db}"
    config.SCREENSHOTS_DIR = test_screenshots
    config.DATA_DIR = tmp_dir

    # Reinitialize engine with test DB
    from database import models
    models.engine = create_engine(config.DATABASE_URL, echo=False)
    models.SessionLocal = sessionmaker(bind=models.engine)
    models.Base.metadata.create_all(models.engine)

    # Seed test retailers
    session = models.SessionLocal()
    from database.models import Retailer
    test_retailers = [
        {"name": "Best Buy", "slug": "bestbuy", "base_url": "https://www.bestbuy.ca/test", "scrape_enabled": True},
        {"name": "Staples", "slug": "staples", "base_url": "https://www.staples.ca/test", "scrape_enabled": True},
        {"name": "Walmart", "slug": "walmart", "base_url": "https://www.walmart.ca/test", "scrape_enabled": True},
        {"name": "Costco", "slug": "costco", "base_url": "https://www.costco.ca/test", "scrape_enabled": False},
    ]
    for r in test_retailers:
        if not session.query(Retailer).filter(Retailer.slug == r["slug"]).first():
            session.add(Retailer(**r))
    session.commit()
    session.close()

    yield {"db_path": test_db, "screenshots_dir": test_screenshots, "tmp_dir": tmp_dir}

    # Clean up test temp directory
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def reset_scrape_lock():
    """Reset the scrape manager lock between tests to prevent cross-test contamination."""
    yield
    from scrapers.manager import release_scrape_lock
    release_scrape_lock()


@pytest.fixture
def client(setup_test_db):
    """FastAPI TestClient with test database."""
    from main import app
    from database.models import get_db, SessionLocal

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session(setup_test_db):
    """Direct database session for test setup/teardown."""
    from database.models import SessionLocal
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def screenshots_dir(setup_test_db):
    """Path to the test screenshots directory."""
    return setup_test_db["screenshots_dir"]
