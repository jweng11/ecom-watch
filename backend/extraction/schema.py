"""Pydantic models for AI-extracted promotion data."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from config import CANONICAL_VENDORS

logger = logging.getLogger(__name__)

# Lowercase lookup for vendor matching
_VENDOR_LOOKUP = {k.lower(): v for k, v in CANONICAL_VENDORS.items()}


class ExtractedPromotion(BaseModel):
    """A single promotion extracted from retailer HTML."""

    retailer: str
    vendor: str
    sku: str
    msrp: Optional[float] = Field(None, gt=0, description="Regular / list price")
    ad_price: Optional[float] = Field(None, gt=0, description="Sale / advertised price")
    discount: Optional[float] = Field(None, ge=0, description="Dollar discount amount")
    discount_pct: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage 0-100")
    cycle: Optional[str] = None
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

    # Metadata (not stored in DB)
    vendor_canonical: bool = True  # False if vendor wasn't in canonical list
    confidence: str = "high"  # high / medium / low

    @model_validator(mode="after")
    def validate_promotion(self) -> "ExtractedPromotion":
        # Canonicalize vendor
        vendor_lower = self.vendor.lower().strip() if self.vendor else ""
        if vendor_lower in _VENDOR_LOOKUP:
            self.vendor = _VENDOR_LOOKUP[vendor_lower]
            self.vendor_canonical = True
        else:
            self.vendor_canonical = False
            logger.warning(f"Unknown vendor: {self.vendor}")

        # Compute discount if both prices present
        if self.msrp and self.ad_price:
            expected_discount = self.msrp - self.ad_price
            if self.discount is None:
                self.discount = round(expected_discount, 2)
            elif abs(self.discount - expected_discount) > 1.0:
                logger.warning(
                    f"Discount mismatch for {self.sku}: stated={self.discount}, "
                    f"computed={expected_discount:.2f}"
                )
                self.discount = round(expected_discount, 2)

            if self.discount_pct is None and self.msrp > 0:
                self.discount_pct = round((self.discount / self.msrp) * 100, 1)

        # Confidence scoring
        issues = 0
        if not self.msrp:
            issues += 1
        if not self.ad_price:
            issues += 1
        if not self.cpu:
            issues += 1
        if not self.ram:
            issues += 1
        if not self.storage:
            issues += 1
        if not self.vendor_canonical:
            issues += 1

        if issues == 0:
            self.confidence = "high"
        elif issues <= 2:
            self.confidence = "medium"
        else:
            self.confidence = "low"

        return self


class ExtractionResult(BaseModel):
    """Result of running AI extraction on a page."""

    model_config = {"protected_namespaces": ()}

    retailer: str
    promotions: list[ExtractedPromotion] = []
    extraction_time: float = 0.0  # seconds
    model_used: str = ""
    raw_response: Optional[str] = None
    error: Optional[str] = None

    @property
    def count(self) -> int:
        return len(self.promotions)

    @property
    def confidence_summary(self) -> dict[str, int]:
        counts = {"high": 0, "medium": 0, "low": 0}
        for p in self.promotions:
            counts[p.confidence] = counts.get(p.confidence, 0) + 1
        return counts
