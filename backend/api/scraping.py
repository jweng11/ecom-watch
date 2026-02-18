"""Scraping API endpoints — trigger scrapes, view runs, serve screenshots."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.models import ScrapeRun, Retailer, get_db
from scrapers.manager import run_scrape, get_scrape_status, claim_scrape_lock, release_scrape_lock
from scrapers.utils.storage import list_screenshots, get_screenshot_filepath

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["scraping"])


# ---------- Request/Response models ----------

class ScrapeRequest(BaseModel):
    retailer: str = "all"          # retailer slug or "all"
    trigger_type: str = "manual"   # "manual" or "scheduled"


# ---------- Background scrape task ----------

async def _background_scrape(retailer_slug: str, trigger_type: str):
    """Run a scrape in the background. Lock is already claimed before this is queued."""
    from database.models import SessionLocal
    db = SessionLocal()
    try:
        await run_scrape(retailer_slug, trigger_type, db)
    except Exception as e:
        logger.error(f"Background scrape failed: {e}")
        release_scrape_lock()  # Release lock on failure so future scrapes can proceed
    finally:
        db.close()


# ---------- Endpoints ----------

@router.post("/scrape/run")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger a scrape for one or all retailers.
    Runs asynchronously in the background and returns immediately.
    """
    # Validate trigger_type
    if request.trigger_type not in ("manual", "scheduled"):
        raise HTTPException(status_code=400, detail="trigger_type must be 'manual' or 'scheduled'")

    # Validate retailer
    if request.retailer != "all":
        retailer = db.query(Retailer).filter(Retailer.slug == request.retailer).first()
        if not retailer:
            valid_slugs = [r.slug for r in db.query(Retailer).all()]
            raise HTTPException(status_code=400, detail=f"Unknown retailer '{request.retailer}'. Valid: {valid_slugs}")
        if not retailer.scrape_enabled:
            raise HTTPException(status_code=400, detail=f"Retailer '{request.retailer}' is disabled for scraping")

    # Atomically check-and-claim the scrape lock to prevent TOCTOU races
    if not claim_scrape_lock():
        raise HTTPException(status_code=409, detail="A scrape is already in progress")

    # Queue background task (lock is already held)
    background_tasks.add_task(_background_scrape, request.retailer, request.trigger_type)

    return {
        "message": f"Scrape queued for {'all retailers' if request.retailer == 'all' else request.retailer}",
        "retailer": request.retailer,
        "trigger_type": request.trigger_type,
    }


@router.get("/scrape/status")
def scrape_status():
    """Get the current scrape status (running/idle, progress)."""
    return get_scrape_status()


@router.get("/scrape/runs")
def list_scrape_runs(
    retailer: Optional[str] = Query(None, description="Filter by retailer name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List scrape runs with optional filters."""
    q = db.query(ScrapeRun).order_by(ScrapeRun.started_at.desc())

    if retailer:
        q = q.filter(ScrapeRun.retailer == retailer)
    if status:
        if status not in ("running", "completed", "failed", "partial"):
            raise HTTPException(status_code=400, detail="Invalid status filter")
        q = q.filter(ScrapeRun.status == status)

    total = q.count()
    runs = q.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "runs": [_serialize_run(r) for r in runs],
    }


@router.get("/scrape/runs/{run_id}")
def get_scrape_run(run_id: int, db: Session = Depends(get_db)):
    """Get details of a single scrape run."""
    run = db.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Scrape run #{run_id} not found")
    return _serialize_run(run)


@router.get("/screenshots")
def get_screenshots(
    retailer: Optional[str] = Query(None, description="Filter by retailer slug"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
):
    """List available screenshots with metadata."""
    screenshots = list_screenshots(retailer_slug=retailer, scrape_date=date)
    return {"total": len(screenshots), "screenshots": screenshots}


@router.get("/screenshots/{retailer}/{date}/{filename}")
def serve_screenshot(retailer: str, date: str, filename: str):
    """Serve a screenshot PNG file."""
    filepath = get_screenshot_filepath(retailer, date, filename)
    if not filepath:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(
        filepath,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800, immutable"},
    )


@router.get("/retailers")
def list_retailers(db: Session = Depends(get_db)):
    """List all retailers with their scrape status."""
    retailers = db.query(Retailer).order_by(Retailer.name).all()
    return {
        "retailers": [
            {
                "id": r.id,
                "name": r.name,
                "slug": r.slug,
                "base_url": r.base_url,
                "scrape_enabled": r.scrape_enabled,
                "last_scraped": r.last_scraped.isoformat() if r.last_scraped else None,
            }
            for r in retailers
        ]
    }


# ---------- Helpers ----------

def _serialize_run(run: ScrapeRun) -> dict:
    return {
        "id": run.id,
        "retailer": run.retailer,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "status": run.status,
        "screenshot_path": run.screenshot_path,
        "html_path": run.html_path,
        "items_found": run.items_found,
        "items_approved": run.items_approved,
        "error_message": run.error_message,
        "trigger_type": run.trigger_type,
    }
