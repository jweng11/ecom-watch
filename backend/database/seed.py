"""Import historical Excel data into SQLite with vendor normalization and audit logging."""
import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from sqlalchemy import text
from database.models import (
    Promotion, Retailer, Cycle, ImportAuditLog, init_db, engine, SessionLocal
)
from config import EXCEL_IMPORT_PATH, CANONICAL_VENDORS

# [FIX] Add logging instead of silently swallowing errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_RETAILERS = [
    {"name": "Best Buy", "slug": "bestbuy", "base_url": "https://www.bestbuy.ca/en-ca/collection/top-deals-laptops/36582"},
    {"name": "Staples", "slug": "staples", "base_url": "https://www.staples.ca/a/content/flyers"},
    {"name": "Walmart", "slug": "walmart", "base_url": "https://www.walmart.ca/browse/electronics/laptops/10003/30622"},
    {"name": "Costco", "slug": "costco", "base_url": "https://www.costco.ca/laptops.html"},
    {"name": "Amazon", "slug": "amazon", "base_url": "https://www.amazon.ca/gp/bestsellers/electronics/677252011"},
    {"name": "Canada Computers", "slug": "canadacomputers", "base_url": "https://www.canadacomputers.com/promotions"},
    {"name": "Memory Express", "slug": "memoryexpress", "base_url": "https://www.memoryexpress.com/Category/LaptopsNotebooks"},
    {"name": "The Source", "slug": "thesource", "base_url": "https://www.thesource.ca/en-ca/computers-tablets/laptops/c/scc-1"},
]


def normalize_vendor(raw_vendor: str) -> tuple[str, bool]:
    if not raw_vendor:
        return "Other", True
    key = raw_vendor.strip().lower()
    if key in CANONICAL_VENDORS:
        canonical = CANONICAL_VENDORS[key]
        changed = canonical != raw_vendor.strip()
        return canonical, changed
    return raw_vendor.strip(), False


def parse_cycle_info(code: str) -> dict:
    if not code:
        return None
    code = code.strip()
    season_map = {
        "SPR": ("Spring", "spring"),
        "BTS": ("Back-to-School", "bts"),
        "HOL": ("Holiday", "holiday"),
    }
    for prefix, (full_name, season) in season_map.items():
        if code.upper().startswith(prefix):
            year_part = code[len(prefix):].strip().strip("'").strip()
            if year_part:
                try:
                    year = int(year_part)
                    if year < 100:
                        year += 2000
                    return {"code": code, "name": f"{full_name} {year}", "season": season, "year": year}
                except ValueError:
                    pass
    return None


def import_excel():
    print(f"Reading Excel file: {EXCEL_IMPORT_PATH}")
    df = pd.read_excel(EXCEL_IMPORT_PATH, sheet_name="Laptops", header=3)
    df.columns = [
        "retailer", "vendor", "sku", "msrp", "ad_price", "discount",
        "cycle", "week", "form_factor", "lcd", "resolution", "touch",
        "os", "cpu", "gpu", "ram", "storage", "other"
    ]
    df = df.dropna(subset=["retailer"])
    print(f"Found {len(df)} rows to import")

    init_db()
    session = SessionLocal()

    # Clear existing data for fresh import
    session.execute(text("DELETE FROM promotions"))
    session.execute(text("DELETE FROM import_audit_log"))
    session.execute(text("DELETE FROM cycles"))
    session.execute(text("DELETE FROM retailers"))
    session.commit()

    # Seed retailers
    for r in DEFAULT_RETAILERS:
        session.add(Retailer(**r))
    session.commit()
    print(f"Seeded {len(DEFAULT_RETAILERS)} retailers")

    # Track cycles
    seen_cycles = {}
    audit_logs = []
    promotions = []

    for idx, row in df.iterrows():
        excel_row = idx + 5  # account for header offset

        # Normalize vendor
        raw_vendor = str(row["vendor"]).strip() if pd.notna(row["vendor"]) else ""
        canonical_vendor, changed = normalize_vendor(raw_vendor)
        if changed and raw_vendor:
            audit_logs.append(ImportAuditLog(
                excel_row=excel_row,
                field_name="vendor",
                original_value=raw_vendor,
                normalized_value=canonical_vendor,
            ))

        # Parse cycle
        cycle_str = str(row["cycle"]).strip() if pd.notna(row["cycle"]) else None
        if cycle_str and cycle_str not in seen_cycles:
            info = parse_cycle_info(cycle_str)
            if info:
                seen_cycles[cycle_str] = info

        # Parse week date
        week_date = None
        if pd.notna(row["week"]):
            if isinstance(row["week"], datetime):
                week_date = row["week"].date()
            else:
                try:
                    week_date = pd.to_datetime(row["week"]).date()
                except Exception:
                    # [FIX] Log date parse failures instead of silently skipping
                    logger.warning(f"Row {excel_row}: Could not parse date '{row['week']}'")

        # Calculate discount percentage
        discount_pct = None
        msrp = float(row["msrp"]) if pd.notna(row["msrp"]) and row["msrp"] != 0 else None
        ad_price = float(row["ad_price"]) if pd.notna(row["ad_price"]) else None
        discount = float(row["discount"]) if pd.notna(row["discount"]) else None
        if msrp and discount:
            discount_pct = round((discount / msrp) * 100, 1)
            # [FIX] Cap discount_pct at 100% to prevent nonsensical values
            if discount_pct > 100:
                logger.warning(f"Row {excel_row}: Discount {discount_pct}% exceeds 100%, capping")
                discount_pct = 100.0
            elif discount_pct < 0:
                logger.warning(f"Row {excel_row}: Negative discount {discount_pct}%, setting to 0")
                discount_pct = 0.0

        # Parse touch
        touch_val = str(row["touch"]).strip() if pd.notna(row["touch"]) else None

        promotions.append(Promotion(
            retailer=str(row["retailer"]).strip(),
            vendor=canonical_vendor,
            sku=str(row["sku"]).strip() if pd.notna(row["sku"]) else "",
            msrp=msrp,
            ad_price=ad_price,
            discount=discount,
            discount_pct=discount_pct,
            cycle=cycle_str,
            week_date=week_date,
            form_factor=str(row["form_factor"]).strip() if pd.notna(row["form_factor"]) else None,
            lcd_size=str(row["lcd"]).strip() if pd.notna(row["lcd"]) else None,
            resolution=str(row["resolution"]).strip() if pd.notna(row["resolution"]) else None,
            touch=touch_val,
            os=str(row["os"]).strip() if pd.notna(row["os"]) else None,
            cpu=str(row["cpu"]).strip() if pd.notna(row["cpu"]) else None,
            gpu=str(row["gpu"]).strip() if pd.notna(row["gpu"]) else None,
            ram=str(row["ram"]).strip() if pd.notna(row["ram"]) else None,
            storage=str(row["storage"]).strip() if pd.notna(row["storage"]) else None,
            notes=str(row["other"]).strip() if pd.notna(row["other"]) else None,
            review_status="approved",
        ))

    # [FIX] Wrap bulk operations in try/except with rollback
    try:
        # Bulk insert promotions
        session.bulk_save_objects(promotions)
        print(f"Imported {len(promotions)} promotions")

        # Insert audit logs
        session.bulk_save_objects(audit_logs)
        print(f"Recorded {len(audit_logs)} normalization changes in audit log")

        # Insert cycles
        for code, info in seen_cycles.items():
            session.add(Cycle(**info))
        print(f"Created {len(seen_cycles)} cycle records")

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Import failed, rolling back: {e}")
        raise
    finally:
        # [FIX] Single close in finally block handles both success and error paths
        session.close()

    # Print summary
    print("\n--- Import Summary ---")
    session = SessionLocal()
    from sqlalchemy import func
    vendor_counts = session.query(
        Promotion.vendor, func.count(Promotion.id)
    ).group_by(Promotion.vendor).order_by(func.count(Promotion.id).desc()).all()
    print("\nPromotions by vendor:")
    for vendor, count in vendor_counts:
        print(f"  {vendor}: {count}")

    retailer_counts = session.query(
        Promotion.retailer, func.count(Promotion.id)
    ).group_by(Promotion.retailer).order_by(func.count(Promotion.id).desc()).all()
    print("\nPromotions by retailer:")
    for retailer, count in retailer_counts:
        print(f"  {retailer}: {count}")

    audit_count = session.query(ImportAuditLog).count()
    print(f"\nVendor normalizations logged: {audit_count}")

    # Show some examples of normalizations
    samples = session.query(ImportAuditLog).limit(10).all()
    if samples:
        print("\nSample normalizations:")
        for s in samples:
            print(f"  Row {s.excel_row}: '{s.original_value}' → '{s.normalized_value}'")

    session.close()
    print("\nImport complete!")


if __name__ == "__main__":
    import_excel()
