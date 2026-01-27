"""
Configuration for Laptop Promo Tracker
Customize your tracking targets and settings here.
"""
import os
from pathlib import Path

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================
OUTPUT_DIR = Path.home() / "Documents" / "laptop_promo_tracker"
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"
EXCEL_FILE = OUTPUT_DIR / "laptop_promotions.xlsx"

# =============================================================================
# LLM SETTINGS (Choose one provider)
# =============================================================================
# Option 1: Anthropic Claude (recommended)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Option 2: OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Which provider to use: "anthropic" or "openai"
LLM_PROVIDER = "anthropic"

# =============================================================================
# SCRAPING TARGETS
# =============================================================================
SITES = [
    {
        "name": "bestbuy_laptops",
        "retailer": "Best Buy",
        "url": "https://www.bestbuy.com/site/promo/laptop-deals",
        "category": "Laptop Deals"
    },
    {
        "name": "walmart_laptops",
        "retailer": "Walmart",
        "url": "https://www.walmart.com/shop/deals/electronics/laptops",
        "category": "Laptop Deals"
    },
    {
        "name": "target_laptops",
        "retailer": "Target",
        "url": "https://www.target.com/c/laptop-computers-deals/-/N-4xwy3",
        "category": "Laptop Deals"
    },
]

# =============================================================================
# SCRAPING SETTINGS
# =============================================================================
BROWSER_VIEWPORT = {"width": 1920, "height": 1080}
PAGE_LOAD_WAIT_MS = 5000  # Wait for dynamic content to load
REQUEST_TIMEOUT_MS = 60000

# User agent to appear as regular browser
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
