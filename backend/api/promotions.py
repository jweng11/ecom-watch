from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Optional
from datetime import date
from database.models import Promotion, get_db

router = APIRouter(prefix="/api/promotions", tags=["promotions"])

# [FIX] Whitelist allowed sort columns to prevent attribute injection
ALLOWED_SORT_COLUMNS = {
    "week_date", "retailer", "vendor", "msrp", "ad_price", "discount",
    "discount_pct", "cycle", "sku", "form_factor", "lcd_size",
}


@router.get("")
def list_promotions(
    retailer: Optional[str] = None,
    vendor: Optional[str] = None,
    cycle: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0, le=100000),  # [FIX] Bounded floats
    max_price: Optional[float] = Query(None, ge=0, le=100000),
    form_factor: Optional[str] = None,
    lcd_size: Optional[str] = None,
    search: Optional[str] = Query(None, max_length=200),  # [FIX] Bounded search string
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = "week_date",
    sort_dir: str = "desc",
    page: int = Query(1, ge=1, le=10000),  # [FIX] Upper bound on page number
    per_page: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    # [FIX] Validate inputs before building the query
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Invalid sort column: {sort_by}")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be before date_to")

    q = db.query(Promotion).filter(Promotion.review_status == "approved")

    if retailer:
        q = q.filter(Promotion.retailer == retailer)
    if vendor:
        q = q.filter(Promotion.vendor == vendor)
    if cycle:
        q = q.filter(Promotion.cycle == cycle)
    if min_price is not None:
        q = q.filter(Promotion.ad_price >= min_price)
    if max_price is not None:
        q = q.filter(Promotion.ad_price <= max_price)
    if form_factor:
        q = q.filter(Promotion.form_factor == form_factor)
    if lcd_size:
        q = q.filter(Promotion.lcd_size == lcd_size)
    if search:
        # [FIX] Escape SQL LIKE wildcards (% and _) in user search input
        safe_search = search.replace("%", r"\%").replace("_", r"\_")
        q = q.filter(
            (Promotion.sku.ilike(f"%{safe_search}%", escape="\\"))
            | (Promotion.cpu.ilike(f"%{safe_search}%", escape="\\"))
            | (Promotion.notes.ilike(f"%{safe_search}%", escape="\\"))
        )
    if date_from:
        q = q.filter(Promotion.week_date >= date_from)
    if date_to:
        q = q.filter(Promotion.week_date <= date_to)
    sort_col = getattr(Promotion, sort_by)
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"
    q = q.order_by(sort_col.asc() if sort_dir == "asc" else sort_col.desc())

    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max((total + per_page - 1) // per_page, 1),
        "items": [_serialize(p) for p in items],
    }


@router.get("/filters")
def get_filter_options(db: Session = Depends(get_db)):
    # [FIX] Filter by approved status consistently with data endpoints
    approved = Promotion.review_status == "approved"
    retailers = [r[0] for r in db.query(distinct(Promotion.retailer)).filter(approved).order_by(Promotion.retailer).all()]
    vendors = [v[0] for v in db.query(distinct(Promotion.vendor)).filter(approved).order_by(Promotion.vendor).all()]
    cycles = [c[0] for c in db.query(distinct(Promotion.cycle)).filter(approved, Promotion.cycle.isnot(None)).order_by(Promotion.cycle).all()]
    form_factors = [f[0] for f in db.query(distinct(Promotion.form_factor)).filter(approved, Promotion.form_factor.isnot(None)).order_by(Promotion.form_factor).all()]
    lcd_sizes = [l[0] for l in db.query(distinct(Promotion.lcd_size)).filter(approved, Promotion.lcd_size.isnot(None)).order_by(Promotion.lcd_size).all()]
    return {
        "retailers": retailers,
        "vendors": vendors,
        "cycles": cycles,
        "form_factors": form_factors,
        "lcd_sizes": lcd_sizes,
    }


# [FIX] Use HTTPException instead of tuple return
@router.get("/{promotion_id}")
def get_promotion(promotion_id: int, db: Session = Depends(get_db)):
    p = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return _serialize(p)


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
        "review_status": p.review_status,
    }
