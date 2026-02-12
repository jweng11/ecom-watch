import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORK_DIR = Path("/sessions/practical-youthful-faraday/ecom-watch-work")
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

CYCLE_DATE_RANGES = {
    "SPR": (1, 4),
    "BTS": (5, 8),
    "HOL": (9, 12),
}
