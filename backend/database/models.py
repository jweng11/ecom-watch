from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey,
    create_engine, Index, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import DATABASE_URL

Base = declarative_base()


class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    retailer = Column(String(100), nullable=False, index=True)
    vendor = Column(String(100), nullable=False, index=True)
    sku = Column(String(255), nullable=False)
    msrp = Column(Float)
    ad_price = Column(Float)
    discount = Column(Float)
    discount_pct = Column(Float)
    cycle = Column(String(20), index=True)
    week_date = Column(Date, index=True)
    form_factor = Column(String(50))
    lcd_size = Column(String(20))
    resolution = Column(String(50))
    touch = Column(String(10))
    os = Column(String(50))
    cpu = Column(String(100))
    gpu = Column(String(100))
    ram = Column(String(50))
    storage = Column(String(100))
    notes = Column(Text)
    promo_type = Column(String(50))
    source_url = Column(Text)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True)
    review_status = Column(String(20), default="approved")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_promotions_retailer_week", "retailer", "week_date"),
        Index("ix_promotions_vendor_cycle", "vendor", "cycle"),
    )


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    retailer = Column(String(100), nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")
    screenshot_path = Column(Text, nullable=True)
    html_path = Column(Text, nullable=True)
    items_found = Column(Integer, default=0)
    items_approved = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    trigger_type = Column(String(20), default="manual")

    promotions = relationship("Promotion", backref="scrape_run")


class Retailer(Base):
    __tablename__ = "retailers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(50), nullable=False, unique=True)
    base_url = Column(Text, nullable=False)
    scrape_enabled = Column(Boolean, default=True)
    scrape_config = Column(JSON, nullable=True)
    last_scraped = Column(DateTime, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="info")
    title = Column(String(255), nullable=False)
    description = Column(Text)
    retailer = Column(String(100), nullable=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    read = Column(Boolean, default=False)


class Cycle(Base):
    __tablename__ = "cycles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True)
    name = Column(String(50), nullable=False)
    season = Column(String(10), nullable=False)
    year = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)


class ImportAuditLog(Base):
    __tablename__ = "import_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    excel_row = Column(Integer)
    field_name = Column(String(50))
    original_value = Column(String(255))
    normalized_value = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
