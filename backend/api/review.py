"""Review queue API — manage pending AI-extracted promotions."""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Promotion, ScrapeRun, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/review", tags=["review"])


# ---------- Request models ----------

class BulkActionRequest(BaseModel):
    promotion_ids: list[int]


class PromotionUpdate(BaseModel):
    vendor: Optional[str] = None
    sku: Optional[str] = None
    msrp: Optional[float] = None
    ad_price: Optional[float] = None
    discount: Optional[float] = None
    discount_pct: Optional[float] = None
    form_factor: Optional[str] = None
    lcd_size: Optional[str] = None
    resolution: Optional[str] = None
    touch: Optional[str] = None
    os: Optional[str] = None
    cpu: Optional[str] = None
    gpu: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    notes: Optional[str] = None
    promo_type: Optional[str] = None
    source_url: Optional[str] = None


# ---------- Endpoints ----------

@router.get("/pending")
def list_pending(
    page: int = Query(1, ge=1, le=10000),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List pending promotions grouped by scrape run."""
    # Find scrape runs that have pending promotions
    runs_with_pending = (
        db.query(
            ScrapeRun.id,
            ScrapeRun.retailer,
            ScrapeRun.started_at,
            ScrapeRun.screenshot_path,
            ScrapeRun.html_path,
            func.count(Promotion.id).label("pending_count"),
        )
        .join(Promotion, Promotion.scrape_run_id == ScrapeRun.id)
        .filter(Promotion.review_status == "pending")
        .group_by(ScrapeRun.id)
        .order_by(ScrapeRun.started_at.desc())
    )

    total = runs_with_pending.count()
    runs = runs_with_pending.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max((total + per_page - 1) // per_page, 1),
        "runs": [
            {
                "scrape_run_id": r.id,
                "retailer": r.retailer,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "screenshot_path": r.screenshot_path,
                "html_path": r.html_path,
                "pending_count": r.pending_count,
            }
            for r in runs
        ],
    }


@router.get("/pending/{scrape_run_id}")
def get_pending_for_run(scrape_run_id: int, db: Session = Depends(get_db)):
    """Get all pending promotions for a specific scrape run."""
    run = db.query(ScrapeRun).filter(ScrapeRun.id == scrape_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Scrape run #{scrape_run_id} not found")

    promotions = (
        db.query(Promotion)
        .filter(
            Promotion.scrape_run_id == scrape_run_id,
            Promotion.review_status == "pending",
        )
        .order_by(Promotion.vendor, Promotion.sku)
        .all()
    )

    return {
        "scrape_run": {
            "id": run.id,
            "retailer": run.retailer,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "screenshot_path": run.screenshot_path,
        },
        "promotions": [_serialize(p) for p in promotions],
    }


@router.put("/{promotion_id}")
def update_promotion(promotion_id: int, update: PromotionUpdate, db: Session = Depends(get_db)):
    """Update a single promotion (inline edit)."""
    promo = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(promo, field, value)

    # Recompute discount if prices changed
    if promo.msrp and promo.ad_price:
        promo.discount = round(promo.msrp - promo.ad_price, 2)
        if promo.msrp > 0:
            promo.discount_pct = round((promo.discount / promo.msrp) * 100, 1)

    db.commit()
    db.refresh(promo)
    return _serialize(promo)


@router.post("/approve")
def bulk_approve(request: BulkActionRequest, db: Session = Depends(get_db)):
    """Bulk approve promotions."""
    count = (
        db.query(Promotion)
        .filter(Promotion.id.in_(request.promotion_ids))
        .update({"review_status": "approved"}, synchronize_session="fetch")
    )
    db.commit()
    return {"approved": count}


@router.post("/reject")
def bulk_reject(request: BulkActionRequest, db: Session = Depends(get_db)):
    """Bulk reject promotions."""
    count = (
        db.query(Promotion)
        .filter(Promotion.id.in_(request.promotion_ids))
        .update({"review_status": "rejected"}, synchronize_session="fetch")
    )
    db.commit()
    return {"rejected": count}


@router.post("/reextract/{scrape_run_id}")
async def reextract(scrape_run_id: int, db: Session = Depends(get_db)):
    """Re-run AI extraction on a scrape run's saved HTML."""
    run = db.query(ScrapeRun).filter(ScrapeRun.id == scrape_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Scrape run #{scrape_run_id} not found")
    if not run.html_path:
        raise HTTPException(status_code=400, detail="No saved HTML for this scrape run")

    html_path = Path(run.html_path)
    if not html_path.exists():
        raise HTTPException(status_code=404, detail=f"HTML file not found: {run.html_path}")

    html_content = html_path.read_text(encoding="utf-8")

    # Determine retailer slug from name
    from database.models import Retailer
    retailer = db.query(Retailer).filter(Retailer.name == run.retailer).first()
    retailer_slug = retailer.slug if retailer else run.retailer.lower().replace(" ", "")

    # Delete existing pending promotions for this run
    deleted = (
        db.query(Promotion)
        .filter(
            Promotion.scrape_run_id == scrape_run_id,
            Promotion.review_status == "pending",
        )
        .delete(synchronize_session="fetch")
    )
    db.commit()
    logger.info(f"Deleted {deleted} pending promotions for re-extraction")

    # Run extraction
    from extraction.ai_extractor import extract_promotions
    result = await extract_promotions(html_content, retailer_slug, run.retailer)

    if result.error:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {result.error}")

    # Store results
    from datetime import date as date_type
    today = date_type.today()
    for promo in result.promotions:
        db_promo = Promotion(
            retailer=promo.retailer,
            vendor=promo.vendor,
            sku=promo.sku,
            msrp=promo.msrp,
            ad_price=promo.ad_price,
            discount=promo.discount,
            discount_pct=promo.discount_pct,
            form_factor=promo.form_factor,
            lcd_size=promo.lcd_size,
            resolution=promo.resolution,
            touch=promo.touch,
            os=promo.os,
            cpu=promo.cpu,
            gpu=promo.gpu,
            ram=promo.ram,
            storage=promo.storage,
            notes=promo.notes,
            promo_type=promo.promo_type,
            source_url=promo.source_url,
            scrape_run_id=scrape_run_id,
            review_status="pending",
            week_date=today,
        )
        db.add(db_promo)
    db.commit()

    return {
        "extracted": result.count,
        "confidence": result.confidence_summary,
        "extraction_time": round(result.extraction_time, 1),
        "model": result.model_used,
    }


# ---------- Helpers ----------

def _serialize(p: Promotion) -> dict:
    return {
        "id": p.id,
        "retailer": p.retailer,
        "vendor": p.vendor,
        "sku": p.sku,
        "msrp": p.msrp,
        "ad_price": p.ad_price,
        "discount": p.discount,
        "discount_pct": p.discount_pct,
        "cycle": p.cycle,
        "week_date": p.week_date.isoformat() if p.week_date else None,
        "form_factor": p.form_factor,
        "lcd_size": p.lcd_size,
        "resolution": p.resolution,
        "touch": p.touch,
        "os": p.os,
        "cpu": p.cpu,
        "gpu": p.gpu,
        "ram": p.ram,
        "storage": p.storage,
        "notes": p.notes,
        "promo_type": p.promo_type,
        "source_url": p.source_url,
        "review_status": p.review_status,
        "scrape_run_id": p.scrape_run_id,
    }
