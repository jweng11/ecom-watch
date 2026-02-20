import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORK_DIR = BASE_DIR / "work"
DATA_DIR = WORK_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
DB_PATH = DATA_DIR / "ecom-watch.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"
DOCS_DIR = BASE_DIR / "docs"
EXCEL_IMPORT_PATH = DOCS_DIR / "CAD Ad Tracking 2025 01252026.xlsx"
OUTPUT_DIR = BASE_DIR  # mounted workspace folder for final outputs

SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

CANONICAL_VENDORS = {
    "acer": "Acer",
    "apple": "Apple",
    "asus": "ASUS",
    "dell": "Dell",
    "alienware": "Alienware",
    "gigabyte": "Gigabyte",
    "hp": "HP",
    "huawei": "Huawei",
    "lg": "LG",
    "lenovo": "Lenovo",
    "microsoft": "Microsoft",
    "msi": "MSI",
    "samsung": "Samsung",
    "other": "Other",
}

# --- Stealth scraping configuration ---
STEALTH_ENABLED = True

STEALTH_USER_AGENTS = [
    # Chrome 121 on Windows 10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome 122 on Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome 121 on macOS Sonoma
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome 122 on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome 121 on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome 122 on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

STEALTH_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1366, "height": 768},
]

SCRAPE_MIN_DELAY = 3   # seconds between page loads (randomized between min and max)
SCRAPE_MAX_DELAY = 8

CYCLE_DATE_RANGES = {
    "SPR": (1, 4),
    "BTS": (5, 8),
    "HOL": (9, 12),
}
