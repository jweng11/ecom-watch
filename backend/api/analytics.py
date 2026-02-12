from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case, extract
from typing import Optional
from database.models import Promotion, Cycle, get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    # [FIX] Filter by approved status consistently with all other endpoints
    approved = Promotion.review_status == "approved"
    total = db.query(func.count(Promotion.id)).filter(approved).scalar()
    retailers = db.query(func.count(distinct(Promotion.retailer))).filter(approved).scalar()
    vendors = db.query(func.count(distinct(Promotion.vendor))).filter(approved).scalar()
    cycles = db.query(func.count(distinct(Promotion.cycle))).filter(approved).scalar()
    avg_discount = db.query(func.avg(Promotion.discount_pct)).filter(approved, Promotion.discount_pct.isnot(None)).scalar()
    latest_date = db.query(func.max(Promotion.week_date)).filter(approved).scalar()
    earliest_date = db.query(func.min(Promotion.week_date)).filter(approved).scalar()

    return {
        "total_promotions": total,
        "total_retailers": retailers,
        "total_vendors": vendors,
        "total_cycles": cycles,
        "avg_discount_pct": round(avg_discount, 1) if avg_discount else 0,
        "date_range": {
            "earliest": earliest_date.isoformat() if earliest_date else None,
            "latest": latest_date.isoformat() if latest_date else None,
        },
    }


@router.get("/by-retailer")
def promotions_by_retailer(
    cycle: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        Promotion.retailer,
        func.count(Promotion.id).label("count"),
        func.avg(Promotion.ad_price).label("avg_price"),
        func.avg(Promotion.discount_pct).label("avg_discount_pct"),
        func.min(Promotion.ad_price).label("min_price"),
        func.max(Promotion.ad_price).label("max_price"),
    ).filter(Promotion.review_status == "approved")

    if cycle:
        q = q.filter(Promotion.cycle == cycle)

    results = q.group_by(Promotion.retailer).order_by(func.count(Promotion.id).desc()).all()

    return [
        {
            "retailer": r.retailer,
            "count": r.count,
            "avg_price": round(r.avg_price, 2) if r.avg_price else 0,
            "avg_discount_pct": round(r.avg_discount_pct, 1) if r.avg_discount_pct else 0,
            "min_price": r.min_price,
            "max_price": r.max_price,
        }
        for r in results
    ]


@router.get("/by-vendor")
def promotions_by_vendor(
    retailer: Optional[str] = None,
    cycle: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        Promotion.vendor,
        func.count(Promotion.id).label("count"),
        func.avg(Promotion.ad_price).label("avg_price"),
        func.avg(Promotion.discount_pct).label("avg_discount_pct"),
    ).filter(Promotion.review_status == "approved")

    if retailer:
        q = q.filter(Promotion.retailer == retailer)
    if cycle:
        q = q.filter(Promotion.cycle == cycle)

    results = q.group_by(Promotion.vendor).order_by(func.count(Promotion.id).desc()).all()

    return [
        {
            "vendor": r.vendor,
            "count": r.count,
            "avg_price": round(r.avg_price, 2) if r.avg_price else 0,
            "avg_discount_pct": round(r.avg_discount_pct, 1) if r.avg_discount_pct else 0,
        }
        for r in results
    ]


@router.get("/discount-trends")
def discount_trends(
    retailer: Optional[str] = None,
    vendor: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        Promotion.cycle,
        func.avg(Promotion.discount_pct).label("avg_discount_pct"),
        func.avg(Promotion.discount).label("avg_discount_dollars"),
        func.avg(Promotion.ad_price).label("avg_price"),
        func.count(Promotion.id).label("count"),
    ).filter(
        Promotion.review_status == "approved",
        Promotion.discount_pct.isnot(None),
    )

    if retailer:
        q = q.filter(Promotion.retailer == retailer)
    if vendor:
        q = q.filter(Promotion.vendor == vendor)

    results = q.group_by(Promotion.cycle).all()

    # [FIX] Dynamic cycle ordering from cycles table instead of hardcoded list
    season_order = {"spring": 0, "bts": 1, "holiday": 2}
    db_cycles = db.query(Cycle).all()
    if db_cycles:
        cycle_order = sorted(
            [c.code for c in db_cycles],
            key=lambda code: next(
                ((c.year, season_order.get(c.season, 9)) for c in db_cycles if c.code == code),
                (9999, 9),
            ),
        )
    else:
        # Fallback: sort result cycles alphabetically if no cycles table data
        cycle_order = sorted([r.cycle for r in results if r.cycle])

    result_map = {r.cycle: r for r in results}

    return [
        {
            "cycle": c,
            "avg_discount_pct": round(result_map[c].avg_discount_pct, 1) if c in result_map and result_map[c].avg_discount_pct else 0,
            "avg_discount_dollars": round(result_map[c].avg_discount_dollars, 2) if c in result_map and result_map[c].avg_discount_dollars else 0,
            "avg_price": round(result_map[c].avg_price, 2) if c in result_map and result_map[c].avg_price else 0,
            "count": result_map[c].count if c in result_map else 0,
        }
        for c in cycle_order
        if c in result_map
    ]


@router.get("/price-distribution")
def price_distribution(
    retailer: Optional[str] = None,
    vendor: Optional[str] = None,
    cycle: Optional[str] = None,
    db: Session = Depends(get_db),
):
    bands = [
        ("$0-500", 0, 500),
        ("$500-1000", 500, 1000),
        ("$1000-1500", 1000, 1500),
        ("$1500-2000", 1500, 2000),
        ("$2000+", 2000, 999999),
    ]

    q = db.query(Promotion).filter(
        Promotion.review_status == "approved",
        Promotion.ad_price.isnot(None),
    )
    if retailer:
        q = q.filter(Promotion.retailer == retailer)
    if vendor:
        q = q.filter(Promotion.vendor == vendor)
    if cycle:
        q = q.filter(Promotion.cycle == cycle)

    results = []
    for label, low, high in bands:
        count = q.filter(Promotion.ad_price >= low, Promotion.ad_price < high).count()
        results.append({"band": label, "count": count})

    return results


@router.get("/vendor-retailer-heatmap")
def vendor_retailer_heatmap(
    cycle: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        Promotion.vendor,
        Promotion.retailer,
        func.count(Promotion.id).label("count"),
    ).filter(Promotion.review_status == "approved")

    if cycle:
        q = q.filter(Promotion.cycle == cycle)

    results = q.group_by(Promotion.vendor, Promotion.retailer).all()

    return [
        {"vendor": r.vendor, "retailer": r.retailer, "count": r.count}
        for r in results
    ]
