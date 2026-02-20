"""Test the AI extraction pipeline against a Canada Computers HTML fixture."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path


async def main():
    fixture_path = Path(__file__).parent / "tests" / "fixtures" / "canadacomputers_sample.html"
    html_content = fixture_path.read_text(encoding="utf-8")
    print(f"Loaded fixture: {len(html_content)} chars")

    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("\n⚠️  GEMINI_API_KEY not set — running schema validation only\n")
        _test_schema_only()
        return

    from extraction.ai_extractor import extract_promotions

    print("Running Gemini extraction...")
    result = await extract_promotions(
        html_content=html_content,
        retailer_slug="canadacomputers",
        retailer_name="Canada Computers",
    )

    if result.error:
        print(f"\n❌ Extraction failed: {result.error}")
        return

    print(f"\n✅ Extracted {result.count} promotions in {result.extraction_time:.1f}s")
    print(f"   Model: {result.model_used}")
    print(f"   Confidence: {result.confidence_summary}")

    for i, promo in enumerate(result.promotions, 1):
        print(f"\n--- Promotion {i} ---")
        print(f"  Vendor: {promo.vendor} (canonical: {promo.vendor_canonical})")
        print(f"  SKU: {promo.sku}")
        print(f"  MSRP: ${promo.msrp}  →  Ad Price: ${promo.ad_price}")
        print(f"  Discount: ${promo.discount} ({promo.discount_pct}%)")
        print(f"  CPU: {promo.cpu}")
        print(f"  GPU: {promo.gpu}")
        print(f"  RAM: {promo.ram}")
        print(f"  Storage: {promo.storage}")
        print(f"  LCD: {promo.lcd_size} / {promo.resolution}")
        print(f"  OS: {promo.os}")
        print(f"  Confidence: {promo.confidence}")


def _test_schema_only():
    """Validate the schema works with sample data (no API needed)."""
    from extraction.schema import ExtractedPromotion, ExtractionResult

    promo = ExtractedPromotion(
        retailer="Canada Computers",
        vendor="asus",
        sku="ASUS Vivobook 15 OLED",
        msrp=799.00,
        ad_price=599.00,
        cpu="AMD Ryzen 5 7530U",
        ram="8GB DDR4",
        storage="512GB SSD",
        lcd_size='15.6"',
        resolution="FHD OLED",
        os="Windows 11 Home",
        form_factor="Laptop",
        promo_type="Sale",
    )

    print(f"  Vendor: {promo.vendor} (canonical: {promo.vendor_canonical})")
    print(f"  Discount: ${promo.discount} ({promo.discount_pct}%)")
    print(f"  Confidence: {promo.confidence}")
    assert promo.vendor == "ASUS", f"Expected ASUS, got {promo.vendor}"
    assert promo.discount == 200.00, f"Expected 200.00, got {promo.discount}"
    assert promo.discount_pct == 25.0, f"Expected 25.0, got {promo.discount_pct}"
    assert promo.confidence == "high"

    # Test unknown vendor
    promo2 = ExtractedPromotion(
        retailer="Canada Computers",
        vendor="UnknownBrand",
        sku="Test Laptop",
        msrp=500.0,
        ad_price=400.0,
    )
    assert not promo2.vendor_canonical
    assert promo2.confidence in ("medium", "low")  # missing fields + unknown vendor

    # Test ExtractionResult
    result = ExtractionResult(
        retailer="Canada Computers",
        promotions=[promo],
        extraction_time=1.5,
        model_used="gemini-2.0-flash",
    )
    assert result.count == 1
    assert result.confidence_summary == {"high": 1, "medium": 0, "low": 0}

    print("\n✅ All schema validation tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
