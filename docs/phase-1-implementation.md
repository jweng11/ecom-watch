# Ecom-Watch: Phase 1 Implementation Report

**Version:** 0.1.0
**Date:** February 12, 2026
**Status:** Complete — Data Platform + Interactive Dashboard

---

## 1. Overview

Phase 1 delivers the foundational data platform and interactive analytics dashboard for Ecom-Watch, a laptop promotion intelligence tool for the Canadian market. It replaces a fully manual workflow — visiting retailer websites, screenshotting promotions, and hand-entering data into Excel — with a structured database, REST API, and browser-based dashboard.

This phase focused on historical data ingestion and visualization. Scraping, AI extraction, and alerting are planned for Phase 2+.

---

## 2. Architecture

```
┌──────────────────────────────────┐
│        React Frontend            │
│   Vite + Tailwind CSS v4         │
│   shadcn/ui-style components     │
│   Recharts for visualization     │
│   Port 5173 (dev server)         │
└──────────┬───────────────────────┘
           │  Vite proxy (/api → :8000)
           ▼
┌──────────────────────────────────┐
│       FastAPI Backend            │
│   SQLAlchemy ORM                 │
│   REST API (JSON)                │
│   Port 8000                      │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│        SQLite Database           │
│   6 tables, 13,161 promotions    │
│   Historical data 2021–2026      │
└──────────────────────────────────┘
```

Both servers bind to `127.0.0.1` (localhost only). The Vite dev server proxies all `/api/*` requests to the backend, so the frontend never makes cross-origin requests in development.

---

## 3. Technology Stack

### Backend (Python 3.10)

| Package | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115.0 | REST API framework |
| Uvicorn | 0.30.6 | ASGI server |
| SQLAlchemy | 2.0.35 | ORM and database access |
| Pydantic | 2.9.2 | Request/response validation |
| Pandas | 2.2.3 | Excel import pipeline |
| openpyxl | 3.1.5 | .xlsx file reader |
| APScheduler | 3.10.4 | Scheduled jobs (Phase 2) |

### Frontend (Node.js)

| Package | Version | Purpose |
|---------|---------|---------|
| React | 19.2.0 | UI framework |
| Vite | 7.3.1 | Build tool and dev server |
| Tailwind CSS | 4.1.18 | Utility-first styling (v4 with oklch) |
| Recharts | 3.7.0 | Chart library |
| Lucide React | 0.563.0 | Icon library |
| CVA | 0.7.1 | Component variant styling |

---

## 4. Database Schema

Six tables across three domains: core data, operational tracking, and configuration.

### Core Data

**promotions** (13,161 rows) — The central table storing every laptop promotion record.

- `id` (PK), `retailer`, `vendor`, `sku`, `msrp`, `ad_price`, `discount`, `discount_pct`
- `cycle`, `week_date`, `form_factor`, `lcd_size`, `resolution`, `touch`, `os`
- `cpu`, `gpu`, `ram`, `storage`, `notes`
- `promo_type`, `source_url`, `scrape_run_id` (FK → scrape_runs)
- `review_status` (default: "approved"), `created_at`, `updated_at`
- Composite indexes: `(retailer, week_date)`, `(vendor, cycle)`

### Operational

**scrape_runs** — Tracks each scraper execution (Phase 2).
**alerts** — Stores generated alerts for price drops, new competitors, etc. (Phase 2).
**import_audit_log** — Records every vendor normalization change during historical import.

### Configuration

**retailers** (8 rows) — Registered retailer websites with scraping configuration.
**cycles** (16 rows) — Promotional cycle metadata (Spring, Back-to-School, Holiday per year).

All timestamp fields use `datetime.now(timezone.utc)` (Python 3.12+ compatible, replacing the deprecated `datetime.utcnow`).

---

## 5. Historical Data Import

The `seed.py` pipeline imports the legacy Excel tracker (`CAD Ad Tracking 2025 01252026.xlsx`) containing records from Spring 2021 through Spring 2026.

### Pipeline Steps

1. Read Excel file (sheet "Laptops", header row 3, 18 columns)
2. Drop rows with missing retailer
3. Normalize vendor names against canonical mapping (14 vendors)
4. Parse cycle codes into structured season/year metadata
5. Parse week dates with fallback and warning logging
6. Calculate discount percentage with 0–100% clamping
7. Bulk insert all records in a single transaction with rollback on failure

### Import Statistics

- 13,161 promotions imported
- 2,332 vendor normalizations logged in audit table
- 16 promotional cycles created
- 8 retailers seeded (Best Buy, Staples, Walmart, Costco, Amazon, Canada Computers, Memory Express, The Source)

### Vendor Normalization

The canonical vendor map handles case/format variations:

| Input variants | Normalized to |
|---------------|--------------|
| "ACER", "acer" | Acer |
| "ASUS", "Asus", "asus" | ASUS |
| "HP", "hp" | HP |
| "LENOVO", "lenovo" | Lenovo |
| (14 vendors total) | |

All normalizations are audit-logged with the original value, normalized value, and Excel row number.

---

## 6. API Endpoints

### Promotions (`/api/promotions`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/promotions` | Filterable, sortable, paginated list |
| GET | `/api/promotions/filters` | Distinct values for filter dropdowns |
| GET | `/api/promotions/{id}` | Single promotion by ID |

**Query parameters for listing:** `retailer`, `vendor`, `cycle`, `min_price`, `max_price`, `form_factor`, `lcd_size`, `search`, `date_from`, `date_to`, `sort_by`, `sort_dir`, `page`, `per_page`

### Analytics (`/api/analytics`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/analytics/summary` | Aggregate stats (totals, averages, date range) |
| GET | `/api/analytics/by-retailer` | Per-retailer breakdown (count, avg price, discount) |
| GET | `/api/analytics/by-vendor` | Per-vendor breakdown |
| GET | `/api/analytics/discount-trends` | Cycle-over-cycle trend data |
| GET | `/api/analytics/price-distribution` | Price band histogram ($0–500, $500–1000, etc.) |
| GET | `/api/analytics/vendor-retailer-heatmap` | Cross-tabulation of vendor × retailer counts |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Server health check |

All data endpoints filter by `review_status == "approved"` consistently, including the `/filters` endpoint for dropdown values.

---

## 7. Frontend Pages

### Dashboard
Summary stat cards (total promotions, avg discount, vendors, cycles, retailers) plus four charts: promotions by retailer, price distribution, top vendors, and average discount by retailer.

### Promotions
Full data grid with 15 columns, 5 filter dropdowns, debounced search (300ms), sortable column headers with whitelist validation, and paginated navigation with first/prev/next/last controls.

### Trends
Four time-series charts showing discount %, average price, promotion count, and discount dollars across all 16 cycles. Filterable by retailer and vendor.

### Comparison
Retailer comparison table with aggregate stats, two comparison charts (count and price/discount by retailer), and a vendor × retailer heatmap with dynamic color intensity scaling.

### Shared Infrastructure
- Error Boundary wrapping the entire app and each page independently (with `key`-based reset on navigation)
- Error state UI on every page with descriptive messages from the API
- Empty state messages for all charts and tables
- Loading spinners with ARIA roles
- Dark theme using oklch color space via Tailwind CSS v4 `@theme`

---

## 8. Security and Input Validation

### Backend

- **CORS:** Restricted to specific localhost origins (`localhost:5173`, `localhost:3000`, `127.0.0.1:5173`); credentials disabled
- **Sort column whitelist:** Only 11 approved column names accepted for `sort_by`; others return HTTP 400
- **SQL LIKE wildcard escaping:** Search input `%` and `_` characters are escaped with backslash to prevent pattern injection
- **Bounded parameters:** `min_price`/`max_price` (0–100,000), `search` (max 200 chars), `page` (1–10,000), `per_page` (1–500)
- **Date range validation:** `date_from` must precede `date_to` (checked before query execution)
- **HTTPException for 404:** Single-promotion lookup returns proper 404, not a tuple
- **Server binding:** Both backend and frontend bind to `127.0.0.1` only (not `0.0.0.0`)

### Frontend

- **ApiError class:** Structured error with status code and server detail extraction
- **Network error handling:** `fetch()` failures caught and wrapped with user-friendly message
- **NaN guards:** `formatCurrency()` and `formatNumber()` handle non-numeric inputs gracefully
- **Debounced search:** 300ms delay prevents API spam during typing

---

## 9. Project Structure

```
ecom-watch/
├── backend/
│   ├── main.py              # FastAPI app, CORS, lifespan, health
│   ├── config.py             # Paths, DB URL, vendor mapping, cycle ranges
│   ├── requirements.txt      # Python dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   ├── promotions.py     # CRUD + filter/sort/search/paginate
│   │   └── analytics.py      # Summary, trends, distribution, heatmap
│   └── database/
│       ├── __init__.py
│       ├── models.py          # SQLAlchemy models (6 tables)
│       └── seed.py            # Excel → SQLite import pipeline
├── frontend/
│   ├── vite.config.js         # Vite + Tailwind v4 + API proxy
│   ├── package.json
│   └── src/
│       ├── main.jsx           # React entry point
│       ├── index.css           # Tailwind @theme (dark oklch palette)
│       ├── App.jsx             # Router + ErrorBoundary
│       ├── lib/
│       │   ├── api.js          # API client with error handling
│       │   └── utils.js        # cn(), formatCurrency(), formatNumber()
│       ├── components/
│       │   ├── AppSidebar.jsx  # Fixed sidebar navigation
│       │   ├── DiscountBadge.jsx
│       │   └── ui/             # shadcn-style primitives
│       │       ├── badge.jsx
│       │       ├── button.jsx
│       │       ├── card.jsx
│       │       ├── input.jsx
│       │       ├── select.jsx
│       │       └── table.jsx
│       └── pages/
│           ├── Dashboard.jsx
│           ├── Promotions.jsx
│           ├── Trends.jsx
│           └── Comparison.jsx
├── docs/
│   ├── ecom-watch-platform-plan.md
│   └── phase-1-implementation.md  (this document)
└── start.sh                   # Launch script for both servers
```

**Total source code:** ~2,005 lines (778 backend, 1,227 frontend).

---

## 10. Running the Application

### Prerequisites
- Python 3.10+
- Node.js 18+
- The historical Excel file at `docs/CAD Ad Tracking 2025 01252026.xlsx`

### Quick Start

```bash
cd ecom-watch

# Install backend dependencies
pip install -r backend/requirements.txt --break-system-packages

# Install frontend dependencies
cd frontend && npm install && cd ..

# Launch both servers
bash start.sh
```

The start script will automatically import the historical Excel data on first run (when no database exists), then start both servers. Open `http://localhost:5173` to access the dashboard.

### Manual Start

```bash
# Terminal 1: Backend
cd backend
python database/seed.py  # First time only
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npx vite --host 127.0.0.1 --port 5173
```

---

## 11. Testing

Phase 1 includes a comprehensive integration test suite covering 59 test cases across all API endpoints. Tests are run via Python's `TestClient` against the FastAPI app.

### Test Coverage

| Category | Tests | What's Verified |
|----------|-------|----------------|
| Health | 3 | Status, version |
| Summary | 8 | All aggregate fields, date range |
| Discount Trends | 7 | Cycle ordering, filtering, field presence |
| By-Retailer | 8 | Field completeness per retailer, cycle filtering |
| Other Analytics | 4 | By-vendor, price distribution (5 bands), heatmap |
| Promotions Listing | 5 | Pagination metadata, item shape |
| Sort Whitelist | 5 | Valid sorts, invalid column rejection, attribute injection prevention |
| Search & Wildcards | 3 | Search results, `%` wildcard escape, `_` wildcard escape |
| Validation | 3 | Date range ordering, page bounds, price bounds |
| Single & 404 | 2 | Existing promotion, non-existent promotion |
| Filters | 5 | All 5 filter categories populated |

All 59 tests pass. Frontend builds cleanly with Vite (no compilation errors or warnings beyond the expected chunk size advisory).

---

## 12. Adversarial Code Review Summary

Three progressive review passes were conducted, identifying and fixing a total of **26 issues** across the codebase.

### Pass 1: Initial Review (20 issues fixed)

The first review was the broadest, covering all backend and frontend files for the first time.

**CRITICAL fixes:**
- CORS wildcard (`*`) replaced with specific localhost origins; credentials disabled
- Sort column parameter was passed directly to `getattr()` — added whitelist validation with HTTP 400 rejection
- Promotions 404 returned a raw tuple instead of HTTPException
- Frontend had zero error handling — no `res.ok` check, no `.catch()`, no Error Boundary

**HIGH fixes:**
- Search input triggered an API call on every keystroke — added 300ms debounce hook
- No empty states for any charts or tables — users saw blank containers
- Missing ARIA labels on all form controls and interactive elements

**MEDIUM fixes:**
- `analytics.py` had a hardcoded 16-element cycle ordering list — replaced with dynamic database query
- `seed.py` silently swallowed date parsing errors — added warning-level logging
- Discount percentages could exceed 100% — added 0–100% clamping
- `DiscountBadge` crashed on negative percentages — added guard

### Pass 2: Security Hardening (9 issues fixed)

The second pass focused on security gaps and consistency issues missed in the first sweep.

**HIGH fixes:**
- `start.sh` bound both servers to `0.0.0.0` (all network interfaces), contradicting the CORS localhost restriction — changed to `127.0.0.1`
- `start.sh` checked for the database at the wrong path — corrected to the actual WORK_DIR location

**MEDIUM fixes:**
- Summary endpoint didn't filter by `review_status == "approved"` — added the filter for consistency
- `@app.on_event("startup")` is deprecated in modern FastAPI — replaced with `lifespan` async context manager
- `datetime.utcnow` is deprecated in Python 3.12+ — replaced with `datetime.now(timezone.utc)` lambdas
- `api.js` didn't catch network errors from `fetch()` — added try/catch with user-friendly message
- Search input allowed SQL LIKE wildcards `%` and `_` — added escape with backslash
- `seed.py` had redundant `session.close()` in both `except` and `finally` blocks
- `formatCurrency()`/`formatNumber()` didn't guard against NaN inputs

### Pass 3: Polish and Cleanup (7 issues fixed)

The third pass caught consistency issues, dead code, and accessibility gaps.

**MEDIUM fixes:**
- `/filters` endpoint didn't filter by approved status — the only remaining unfiltered endpoint
- Dashboard retry button used `window.location.reload()` — replaced with React state-based re-fetch

**LOW fixes:**
- Removed unused imports across 3 files (Dashboard: `LineChart`/`Line`; Promotions: `useCallback`/`useRef`/`ArrowUpDown`)
- Removed dead `ChartOrEmpty` component in Trends (defined but never referenced)
- Removed unused `C.red` color constant in Comparison
- Added `aria-hidden="true"` to all sidebar icons, `aria-current="page"` to active nav item, `aria-disabled` to coming-soon items

---

## 13. Lessons Learned

### SQLite on mounted filesystems
SQLite requires filesystem-level locking that many network/mounted filesystems don't support. When the database was placed in the mounted workspace folder, writes failed with disk I/O errors. The fix was to store the database in a local working directory and only place the source code (not the live database) in the mounted folder. For production, a proper database server (PostgreSQL) would avoid this entirely.

### Hardcoded data is technical debt even in prototypes
The hardcoded 16-element cycle ordering array in `analytics.py` worked perfectly for the initial dataset but would have silently broken the moment a new cycle (e.g., BTS'26) was imported. Pulling the ordering from the database is only marginally more complex but future-proof. The same lesson applies to the vendor normalization map — it should eventually be database-driven rather than a Python dictionary.

### Input validation must be exhaustive, not just present
The first review found the obvious issues (no sort whitelist, no error handling), but the second pass revealed subtler problems: LIKE wildcards in search input, date range ordering validated *after* query execution, and the `/filters` endpoint missing the same `review_status` filter that every other endpoint used. Consistency across endpoints is as important as validation within a single endpoint.

### Error handling is a feature, not an afterthought
The initial frontend implementation had zero error handling — no `.catch()`, no Error Boundary, no empty states, no loading indicators with accessible roles. This meant any API error would crash the entire app silently. Adding structured error handling across every page roughly doubled the code complexity of each component but made the application production-viable.

### Deprecated APIs accumulate quietly
Two deprecations were caught: `@app.on_event("startup")` (deprecated in FastAPI 0.103+, replaced by lifespan context managers) and `datetime.utcnow` (deprecated in Python 3.12+, replaced by `datetime.now(timezone.utc)`). Both still work today but will generate warnings and eventually break. Catching these during review rather than after a runtime warning is cheaper.

### Security reviews need multiple passes
The first review found the obvious CORS wildcard and sort injection. The second found `0.0.0.0` binding in `start.sh` (contradicting the CORS fix) and LIKE wildcard injection (a subtler variant of the injection class). The third found the one remaining endpoint that lacked the `review_status` filter. Each pass found real issues that the previous pass missed, suggesting a minimum of two review passes for any security-relevant codebase.

---

## 14. Known Limitations

- **No automated scraping yet.** All data comes from the historical Excel import. Phase 2 will add Playwright-based scraping with Claude API extraction.
- **No authentication.** The API is accessible to anyone on localhost. Phase 2+ will add user authentication for the review workflow.
- **SQLite for development only.** The single-writer limitation and file-based storage won't scale for concurrent users. Production deployment should use PostgreSQL.
- **Client-side routing only.** Page navigation uses React state (`useState`) rather than URL-based routing. Deep linking and browser back/forward don't work. A router (React Router or TanStack Router) should be added before Phase 2.
- **No data export.** The original workflow produced Excel files and PowerPoint decks. Export functionality is planned for Phase 2.
- **Bundle size.** The production JS bundle is 626 KB (188 KB gzipped), with Recharts being the largest dependency. Code splitting via dynamic imports would reduce initial load time.

---

## 15. Phase 2 Roadmap

The following features are planned based on the original platform plan:

1. **Playwright scraper** for 7 Canadian retailers with screenshot capture
2. **Claude API integration** for structured data extraction from captured pages
3. **Human-in-the-loop review UI** for approving/editing AI-extracted promotions
4. **APScheduler integration** for weekly automated scrape runs
5. **Excel export** matching the original tracker format
6. **PowerPoint export** for weekly ad scan decks
7. **Email notifications** for weekly digests and critical price alerts
8. **URL-based routing** with React Router
9. **PostgreSQL migration** for production deployment
