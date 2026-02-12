# Ecom-Watch: Laptop Promotion Intelligence Platform

## Project Plan

**Author:** Jonathan Weng
**Date:** February 11, 2026
**Version:** 1.0 — Draft for Review

---

## 1. Executive Summary

Ecom-Watch is a local web application that automates the monitoring, collection, and analysis of laptop promotional offerings across major Canadian retailers. It replaces a fully manual workflow — visiting retailer websites, screenshotting ads, and hand-entering promotion data into Excel — with an intelligent platform that scrapes retailer sites on a schedule, uses AI to extract structured data, stores everything in a queryable database, and presents insights through an interactive dashboard.

The platform will import 5+ years of historical promotion data (13,000+ records) from the existing Excel tracker, enabling powerful trend analysis from day one. It supports both scheduled automation and on-demand scanning, human-in-the-loop data review, and exports to Excel and PowerPoint for stakeholder sharing.

---

## 2. Problem Statement

### Current Workflow

The current promotion tracking process is entirely manual:

1. **Weekly site visits** — A team member visits each retailer's website (Best Buy, Staples, Walmart, Costco, Amazon, etc.) and navigates to their laptop deals or flyer pages.
2. **Screenshot capture** — Promotional pages are screenshotted and assembled into a weekly PowerPoint deck organized by retailer, with date ranges noted on each slide.
3. **Manual data entry** — Each promoted laptop's details (retailer, vendor, SKU, MSRP, ad price, discount, specs) are manually typed into an Excel spreadsheet row by row.
4. **Historical maintenance** — The Excel file has grown to 13,000+ rows spanning Spring 2017 through Spring 2026, making it increasingly difficult to query, filter, and derive insights from.

### Pain Points

- **Time-intensive** — The full weekly cycle (browsing, screenshotting, data entry) consumes significant hours that could be spent on strategic analysis.
- **Error-prone** — Manual transcription of specs, prices, and SKUs introduces data quality risks.
- **Analysis-limited** — Excel at 13K+ rows is slow to filter, difficult to visualize trends, and cumbersome for multi-dimensional competitive comparisons.
- **No alerting** — Changes in the competitive landscape (new promotions, price drops, ended deals) are only noticed during the next manual check.
- **Scaling difficulty** — Adding new retailers (like Canada Computers or Memory Express) means proportionally more manual work.

---

## 3. Solution Overview

Ecom-Watch is a locally-hosted web application with four core capabilities:

### Automated Data Collection
Playwright-based browser automation visits each retailer's promotions pages, captures full-page screenshots, and saves page content. Runs on a configurable schedule (default: weekly) with on-demand scanning available anytime.

### AI-Powered Data Extraction
Captured page content is processed through an AI pipeline (Claude API) that extracts structured promotion data matching the established 18-column schema. Extracted data is staged for human review before being committed to the database.

### Historical Database
All promotion data — both newly scraped and historically imported — lives in a SQLite database optimized for fast querying, filtering, and aggregation. Replaces Excel as the primary data store while maintaining full export capability.

### Interactive Dashboard
A React-based web UI providing current promotion views, trend analysis charts, competitive comparisons, a screenshot archive, weekly digests, and one-click exports to Excel and PowerPoint.

---

## 4. Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User's Browser                        │
│                  (Dashboard UI - React)                   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│                 Backend API (FastAPI)                     │
│                                                          │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Scraping  │  │ AI Extraction│  │  Report Generator │  │
│  │ Engine    │  │ Pipeline     │  │  (Excel/PPTX/PDF) │  │
│  │(Playwright│  │ (Claude API) │  │                   │  │
│  └─────┬────┘  └──────┬───────┘  └───────────────────┘  │
│        │              │                                   │
│  ┌─────▼──────────────▼──────────────────────────────┐   │
│  │              SQLite Database                       │   │
│  │  promotions │ scrape_runs │ retailers │ cycles     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐   │
│  │           Scheduler (APScheduler)                  │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐  ┌───────────┐  ┌──────────┐
   │bestbuy  │  │staples    │  │amazon    │  ... (7 retailers)
   │.ca      │  │.ca        │  │.ca       │
   └─────────┘  └───────────┘  └──────────┘
```

### Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend API | Python + FastAPI | Async-capable, great ecosystem for data work, easy to extend |
| Database | SQLite | No server needed, portable, handles 100K+ rows easily |
| Frontend | React + Tailwind CSS + Recharts | Modern, responsive dashboard with rich charting |
| Scraping | Playwright (Python) | Handles JavaScript-heavy retail sites, headless browser |
| AI Extraction | Claude API (Sonnet) | Resilient to layout changes, understands context, structured output |
| Scheduling | APScheduler | Built into the Python app, cron-like scheduling |
| Excel Export | openpyxl | Maintains formatting compatibility with existing tracker |
| PPTX Export | python-pptx | Generates slide decks matching current ad scan format |
| Data Migration | pandas + openpyxl | Imports historical Excel data into SQLite |

### Directory Structure

```
ecom-watch/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # App configuration
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── migrations.py        # Schema management
│   │   └── seed.py              # Historical data import
│   ├── scrapers/
│   │   ├── base.py              # Base scraper class
│   │   ├── bestbuy.py           # Best Buy scraper
│   │   ├── staples.py           # Staples scraper
│   │   ├── walmart.py           # Walmart scraper
│   │   ├── costco.py            # Costco scraper
│   │   ├── amazon.py            # Amazon scraper
│   │   ├── canadacomputers.py   # Canada Computers scraper
│   │   └── memoryexpress.py     # Memory Express scraper
│   ├── extraction/
│   │   ├── ai_extractor.py      # Claude API extraction pipeline
│   │   └── schema.py            # Data validation schemas
│   ├── api/
│   │   ├── promotions.py        # Promotion CRUD endpoints
│   │   ├── scraping.py          # Scrape trigger/status endpoints
│   │   ├── analytics.py         # Dashboard data endpoints
│   │   ├── exports.py           # Excel/PPTX export endpoints
│   │   └── alerts.py            # Alert management endpoints
│   ├── services/
│   │   ├── scheduler.py         # APScheduler configuration
│   │   ├── digest.py            # Weekly digest generation
│   │   └── comparison.py        # Competitive analysis logic
│   └── exports/
│       ├── excel_export.py      # Excel file generation
│       └── pptx_export.py       # PowerPoint file generation
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # Weekly overview/digest
│   │   │   ├── Promotions.jsx       # Current promotions grid
│   │   │   ├── Trends.jsx           # Historical trend charts
│   │   │   ├── Comparison.jsx       # Competitive comparison
│   │   │   ├── Screenshots.jsx      # Visual ad archive
│   │   │   ├── ReviewQueue.jsx      # AI extraction review
│   │   │   └── Settings.jsx         # Retailer config, schedule
│   │   ├── components/
│   │   │   ├── PromotionTable.jsx
│   │   │   ├── PriceTrendChart.jsx
│   │   │   ├── DiscountDistribution.jsx
│   │   │   ├── VendorMixChart.jsx
│   │   │   ├── RetailerComparison.jsx
│   │   │   ├── WeeklyDigestCard.jsx
│   │   │   └── AlertBanner.jsx
│   │   └── utils/
│   │       └── api.js               # API client
│   └── package.json
├── data/
│   ├── ecom-watch.db               # SQLite database
│   └── screenshots/                 # Organized screenshot archive
│       ├── bestbuy/
│       ├── staples/
│       └── ...
├── docs/
│   ├── ecom-watch-platform-plan.md  # This document
│   └── ...                          # Existing files
├── requirements.txt
└── README.md
```

---

## 5. Data Model

### Promotions Table (Core)

This table mirrors and extends the existing Excel schema:

| Column | Type | Description | Maps to Excel Column |
|--------|------|-------------|---------------------|
| id | INTEGER (PK) | Auto-increment unique ID | (new) |
| retailer | TEXT | Retailer name | A — Retailer |
| vendor | TEXT | Laptop brand/manufacturer | B — Vendor |
| sku | TEXT | Model/SKU identifier | C — SKU |
| msrp | REAL | Manufacturer's suggested retail price | D — MSRP |
| ad_price | REAL | Promotional/advertised price | E — Ad Price |
| discount | REAL | Dollar discount amount | F — Discount |
| discount_pct | REAL | Percentage discount (calculated) | (new — derived) |
| cycle | TEXT | Promotional cycle (e.g., "SPR'26") | G — Cycle |
| week_date | DATE | Week the promotion was active | H — Week |
| form_factor | TEXT | Clamshell, Convertible, etc. | I — Form Factor |
| lcd_size | TEXT | Screen size (e.g., "15.6\"") | J — LCD |
| resolution | TEXT | Display resolution | K — Resolution |
| touch | BOOLEAN | Touchscreen yes/no | L — Touch |
| os | TEXT | Operating system | M — OS |
| cpu | TEXT | Processor model | N — CPU |
| gpu | TEXT | Graphics (UMA or discrete) | O — GPU |
| ram | TEXT | Memory config | P — RAM |
| storage | TEXT | Storage config | Q — Storage |
| notes | TEXT | Additional notes (Top Deal, Copilot+, etc.) | R — Other |
| promo_type | TEXT | Promotion category (Top Deal, Clearance, Rollback, Flyer, etc.) | (new) |
| source_url | TEXT | URL of the promotion page | (new) |
| scrape_run_id | INTEGER (FK) | Link to the scrape that found this | (new) |
| review_status | TEXT | pending / approved / corrected / rejected | (new) |
| created_at | DATETIME | When the record was created | (new) |
| updated_at | DATETIME | When the record was last modified | (new) |

### Scrape Runs Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment unique ID |
| retailer | TEXT | Which retailer was scraped |
| started_at | DATETIME | When the scrape began |
| completed_at | DATETIME | When the scrape finished |
| status | TEXT | running / completed / failed / partial |
| screenshot_path | TEXT | Path to the captured screenshot(s) |
| html_path | TEXT | Path to the saved HTML |
| items_found | INTEGER | Number of promotions extracted |
| items_approved | INTEGER | Number approved after review |
| error_message | TEXT | Error details if failed |
| trigger_type | TEXT | scheduled / manual |

### Retailers Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment unique ID |
| name | TEXT | Display name (e.g., "Best Buy") |
| slug | TEXT | URL-safe identifier (e.g., "bestbuy") |
| base_url | TEXT | Retailer's promotion page URL |
| scrape_enabled | BOOLEAN | Whether to include in scheduled scrapes |
| scrape_config | JSON | Retailer-specific scraping parameters |
| last_scraped | DATETIME | Timestamp of most recent successful scrape |

### Alerts Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment unique ID |
| alert_type | TEXT | new_promo / price_drop / deal_ended / anomaly / new_vendor |
| severity | TEXT | info / notable / critical |
| title | TEXT | Brief summary |
| description | TEXT | Detailed explanation |
| retailer | TEXT | Related retailer (if applicable) |
| promotion_id | INTEGER (FK) | Related promotion (if applicable) |
| created_at | DATETIME | When the alert was generated |
| read | BOOLEAN | Whether the user has seen it |

### Cycles Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment unique ID |
| code | TEXT | Cycle code (e.g., "SPR'26") |
| name | TEXT | Full name (e.g., "Spring 2026") |
| season | TEXT | spring / bts / holiday |
| year | INTEGER | Calendar year |
| start_date | DATE | Approximate cycle start |
| end_date | DATE | Approximate cycle end |

---

## 6. Feature Details

### 6.1 Scraping Engine

Each retailer gets a dedicated scraper class that inherits from a base class. The base class handles common operations (launching the browser, taking screenshots, saving HTML, error handling, retries) while each retailer subclass handles site-specific navigation.

**Retailer Configurations:**

| Retailer | URL Pattern | Notes |
|----------|-------------|-------|
| Best Buy (bestbuy.ca) | Computers & Tablets > Laptops > "Top Deals" filter | JavaScript-heavy, uses carousels; filter by "Top Deals" and "Best Buy Only" |
| Staples (staples.ca) | /a/content/flyers (digital flyer) | Weekly flyer format, paginated; laptop section needs to be navigated to |
| Walmart (walmart.ca) | Rollback/clearance pages for laptops | Promotions rotate frequently; may have "No CE" weeks |
| Costco (costco.ca) | Laptops category with member pricing | Limited selection, less frequent changes; warehouse deals |
| Amazon (amazon.ca) | Bestsellers in Laptops + Deals page | Bestseller rankings plus Lightning/Today's Deals; highly dynamic |
| Canada Computers | canadacomputers.com laptop deals/sales | Frequent sales, detailed spec listings |
| Memory Express | memoryexpress.com laptop deals | Western Canada focus, competitive pricing, good spec data |

**Scrape Flow:**

```
1. Launch headless Chromium via Playwright
2. Navigate to retailer's promotion URL
3. Handle cookie banners, pop-ups, age gates
4. Scroll to load lazy content / paginate through results
5. Capture full-page screenshot(s) → save to data/screenshots/{retailer}/{date}/
6. Extract page HTML → save to data/html/{retailer}/{date}/
7. Send HTML/text content to AI extraction pipeline
8. Log scrape run to database
9. Return extracted data for review
```

**Error Handling:**
- Automatic retry (up to 3 attempts) on network failures
- Screenshot capture even on partial failures for manual review
- Dead-link detection and alerting if a retailer URL changes
- Rate limiting (minimum 5-second delay between page loads) to be respectful of retailer servers

### 6.2 AI Data Extraction Pipeline

The extraction pipeline processes captured page content through Claude's API to produce structured promotion data.

**Process:**

```
1. Receive raw HTML/text from scraping engine
2. Pre-process: strip navigation, footer, irrelevant sections
3. Construct prompt with:
   - The page content
   - The target schema (18+ fields)
   - Examples of correctly extracted records (few-shot)
   - Retailer-specific guidance (e.g., "Best Buy 'Top Deal' badges indicate promoted items")
4. Call Claude API (Sonnet model for cost efficiency)
5. Parse structured JSON response
6. Validate data types, ranges, required fields
7. Flag low-confidence extractions (missing price, unrecognized vendor, etc.)
8. Stage all records with review_status = "pending"
```

**Validation Rules:**
- MSRP and ad_price must be positive numbers
- Discount must equal MSRP minus ad_price (within $0.01 tolerance)
- Vendor must match known vendor list (or flag as "new vendor" alert)
- CPU, GPU, RAM, storage must follow established naming patterns
- Week date must fall within the current cycle's date range

**Fallback Strategy:**
If the Claude API is unavailable or rate-limited, the system saves the raw HTML and screenshots for manual processing later. The review queue will show these as "extraction pending" items.

### 6.3 Human Review Queue

All AI-extracted data enters a review queue before being committed to the database. The review interface shows:

- Side-by-side view: screenshot on the left, extracted data table on the right
- Color-coded confidence indicators (green = high confidence, yellow = needs attention, red = likely error)
- Inline editing for corrections
- Bulk approve for high-confidence batches
- "Reject" option to discard incorrect extractions
- Notes field for the reviewer to add context

**Workflow:**
```
AI extracts 25 promotions from Best Buy
  → 20 are high-confidence (all fields extracted, validated)
  → 3 are medium-confidence (one field uncertain)
  → 2 are low-confidence (missing spec data)

Reviewer bulk-approves the 20, manually corrects the 3,
and either fixes or rejects the 2.
All approved records committed to database.
```

### 6.4 Dashboard Views

#### Home / Weekly Digest
The landing page shows a summary of the most recent scrape cycle:
- Total new promotions found (by retailer)
- Notable alerts (biggest price drops, new vendors, ended deals)
- Quick stats: average discount this week, deepest discount, most promoted vendor
- Links to drill into each section

#### Current Promotions
An interactive, filterable data grid showing all active promotions:
- Filters: retailer, vendor, price range, screen size, form factor, CPU brand, GPU type
- Sortable by any column
- Expandable rows showing full specs
- Quick comparison checkbox to compare selected models side-by-side
- Color-coded discount depth (deeper discounts highlighted)

#### Trend Analysis
Historical charts powered by the full 5-year dataset:
- **Average discount by cycle** — Line chart showing how aggressive promotions are over time
- **Price point distribution** — Histogram showing where laptops cluster by price tier ($0-500, $500-1000, $1000-1500, $1500-2000, $2000+)
- **Vendor promotion frequency** — Heatmap showing which vendors appear most often at which retailers
- **Spec trends** — Track how promoted laptop specs evolve (e.g., RAM moving from 8GB to 16GB as standard)
- **Seasonal patterns** — Compare Spring vs. Back-to-School vs. Holiday cycles year-over-year
- All charts filterable by retailer, vendor, form factor, and date range

#### Competitive Comparison
Purpose-built views for strategic planning:
- **Retailer vs. Retailer** — Compare two retailers' laptop promotion strategies side-by-side (price distribution, vendor mix, average discount depth)
- **Vendor Focus** — For a specific vendor (e.g., Acer), show how their products are promoted across all retailers — where do they get the best placement, deepest discounts, most SKU variety?
- **Price Band Analysis** — For a given price band (e.g., $800-$1200), what are all retailers offering and how do the specs compare?
- **Promotional Calendar** — Timeline view showing when each retailer tends to run their strongest promotions

#### Screenshot Archive
A browsable gallery replacing the PowerPoint archive:
- Grid of screenshot thumbnails organized by retailer
- Filter by date range, retailer
- Click to enlarge any screenshot
- Side-by-side comparison of the same retailer's page across different weeks

#### Settings
- Retailer management (add/remove/configure scrapers)
- Schedule configuration (which days, which times)
- AI extraction settings (API key, model preference)
- Export format preferences
- User preferences (default filters, notification settings)

### 6.5 Alerts System

Alerts are generated automatically after each scrape by comparing new data to historical patterns.

**Alert Types:**

| Type | Trigger | Severity |
|------|---------|----------|
| New Promotion | A product appears that wasn't in the previous week's data | Info |
| Deal Ended | A product was promoted last week but is no longer listed | Info |
| Price Drop | A product's ad price decreased by more than 5% week-over-week | Notable |
| Price Increase | A product's ad price increased week-over-week | Notable |
| Deep Discount | Discount exceeds 30% off MSRP (configurable threshold) | Notable |
| New Vendor at Retailer | A vendor appears at a retailer where they haven't been seen before | Notable |
| New Product Launch | A SKU appears for the first time across all retailers | Notable |
| Anomaly | Unusual pattern (e.g., retailer has 50% more deals than typical) | Critical |

Alerts appear as a notification badge in the dashboard header and are collected in the Weekly Digest view. Critical alerts also trigger immediate email notifications, and all alerts are summarized in the weekly digest email (see Section 13, Decision #5).

### 6.6 Export Pipeline

#### Excel Export
- Generates .xlsx files matching the existing "CAD Ad Tracking" format exactly
- Options: export all data, export by date range, export by retailer/vendor filter
- Maintains the same column order and naming for backward compatibility
- Includes the "Input" reference sheet with retailer/cycle/vendor lookup lists
- Formatted with headers, column widths, and data validation matching the original

#### PowerPoint Export
- Auto-generates weekly ad scan decks matching the current format
- Title slide with date and branding
- Section dividers for each retailer
- Screenshot slides with retailer name and date range overlay
- Optional: adds a summary data table slide per retailer showing extracted promotions

#### PDF Reports (Future Enhancement)
- Competitive analysis reports formatted for stakeholder presentations
- Includes charts, tables, and key insights narrative

---

## 7. Tracked Retailers

| # | Retailer | Domain | Current Status | Promotion Source |
|---|----------|--------|---------------|-----------------|
| 1 | Best Buy | bestbuy.ca | Currently tracked | Top Deals / Weekly Ads |
| 2 | Staples | staples.ca | Currently tracked | Weekly Flyer |
| 3 | Walmart | walmart.ca | Currently tracked | Rollbacks / Weekly Flyer |
| 4 | Costco | costco.ca | Currently tracked | Member Deals |
| 5 | Amazon | amazon.ca | Partially tracked | Bestsellers / Deals |
| 6 | Canada Computers | canadacomputers.com | New addition | Sale/Deals Page |
| 7 | Memory Express | memoryexpress.com | New addition | Sale/Deals Page |

---

## 8. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Core infrastructure — database, API skeleton, historical data import

- Set up project structure (FastAPI backend, React frontend scaffold)
- Define SQLite schema and create database models
- Build the historical data import pipeline (Excel → SQLite)
- Import all 13,000+ existing records with data cleaning and normalization
- Basic API endpoints for querying promotions (list, filter, search)
- Simple promotions grid view in the frontend

**Deliverable:** Working app that serves the existing historical data through a filterable web interface.

### Phase 2: Scraping Engine (Weeks 3-4)
**Goal:** Automated retailer site scraping with screenshot capture

- Implement base scraper class with Playwright
- Build scrapers for all 7 retailers
- Screenshot capture and organized file storage
- Scrape run logging and status tracking
- Manual trigger endpoint ("Scan Now" button)
- Screenshot archive view in the frontend

**Deliverable:** Ability to trigger scrapes from the dashboard and browse captured screenshots.

### Phase 3: AI Extraction + Review (Weeks 5-6)
**Goal:** Automated data extraction with human review workflow

- Claude API integration for structured data extraction
- Extraction prompt engineering and few-shot examples
- Data validation and confidence scoring
- Review queue interface (side-by-side screenshot + data, inline editing)
- Bulk approve/reject workflow
- Connect approved data to the promotions database

**Deliverable:** End-to-end pipeline from scrape → extract → review → database.

### Phase 4: Dashboard & Analytics (Weeks 7-8)
**Goal:** Rich analytical views and trend visualizations

- Weekly Digest / Home dashboard
- Trend Analysis charts (discount trends, price distributions, vendor frequency, spec evolution)
- Competitive Comparison views (retailer vs. retailer, vendor focus, price band analysis)
- Filtering and drill-down across all views
- Responsive design for comfortable use on various screen sizes

**Deliverable:** Full analytical dashboard with 5 years of historical insight.

### Phase 5: Alerts, Scheduling & Email (Week 9)
**Goal:** Automated monitoring, change detection, and email notifications

- APScheduler integration for weekly scheduled scrapes
- Alert generation engine (comparing new data vs. historical patterns)
- Alert notification UI (badge, digest card, alert list)
- Configurable thresholds for alert triggers
- SMTP email integration for weekly digest and critical alert emails
- Schedule management UI in Settings

**Deliverable:** Fully automated weekly monitoring with smart alerting and email notifications.

### Phase 6: Exports & Polish (Week 10)
**Goal:** Export capabilities and overall refinement

- Excel export matching existing format
- PowerPoint deck auto-generation with screenshots
- Settings page for retailer management and preferences
- Error handling improvements and edge case fixes
- Performance optimization for large dataset queries
- Documentation and README

**Deliverable:** Production-ready application with full export pipeline.

---

## 9. Typical Weekly Workflow (Post-Implementation)

```
Monday 6:00 AM — Scheduled scrape runs automatically
  ├── Playwright visits all 7 retailer sites
  ├── Screenshots captured and stored
  ├── AI extracts promotion data from each page
  └── All data staged in review queue

Monday 9:00 AM — Jonathan opens dashboard
  ├── Sees "Weekly Digest" card:
  │     "42 new promotions found across 7 retailers"
  │     "3 alerts: Best Buy deep discount on ASUS, new Dell model at Costco,
  │      Memory Express clearance event"
  ├── Opens Review Queue
  │     → Bulk approves 35 high-confidence extractions
  │     → Corrects 5 medium-confidence items
  │     → Rejects 2 duplicates
  └── All approved data committed to database

Monday 9:30 AM — Analysis and planning
  ├── Opens Trend Analysis: checks discount depth trends for Q1 2026
  ├── Opens Competitive Comparison: compares Best Buy vs. Canada Computers
  │     pricing on 15-16" laptops
  ├── Exports Excel report for team meeting
  └── Generates PowerPoint deck for stakeholder review

Wednesday 2:00 PM — Flash sale alert
  ├── Manually triggers "Scan Now" for Best Buy
  ├── Reviews 8 new clearance promotions
  └── Approves and shares with team via Excel export
```

---

## 10. Technical Considerations

### Web Scraping Ethics
- All scrapes use reasonable rate limiting (minimum 5-second delays between requests)
- Respect robots.txt directives where applicable
- Identify the scraper with an honest User-Agent string
- Scrape only publicly-available promotion pages (no login-gated content)
- Data is used for internal competitive analysis only

### Data Quality
- AI extraction includes confidence scoring to flag uncertain data
- Human review catches extraction errors before they enter the database
- Validation rules enforce data type and range constraints
- Duplicate detection prevents the same promotion from being recorded twice
- Historical data import includes full vendor name normalization with audit log (see Section 13, Decision #2)

### Resilience
- Scraper failures are logged with screenshots of the failure state
- Partial scrapes save whatever was successfully captured
- AI extraction failures fall back to manual review of screenshots
- Database backups before each major import operation
- The app functions fully offline for analysis/exports (only scraping needs internet)

### Scalability
- SQLite handles hundreds of thousands of rows comfortably for this use case
- If the dataset grows beyond 500K rows or multiple concurrent users are needed, migration to PostgreSQL is straightforward with SQLAlchemy
- Adding a new retailer requires only a new scraper subclass and a database config entry
- The AI extraction prompt can be tuned per-retailer for optimal accuracy

---

## 11. Future Enhancements (Post-MVP)

These are capabilities to consider after the core platform is stable:

- **Price prediction** — Use historical patterns to forecast likely promotion pricing for upcoming cycles
- **Product matching** — Automatically match the same product across different retailers for direct price comparison
- **Market share dashboards** — Track each vendor's share of promotional slots by retailer over time
- **Multi-category support** — Extend beyond laptops to tablets, desktops, monitors, or other CE categories
- **Team access** — Add user accounts so multiple team members can review and annotate data
- **API access** — Expose promotion data via API for integration with other tools (BI platforms, Slack bots)
- **PDF competitive reports** — Auto-generate formatted reports with charts and narrative for executive presentations

---

## 12. Success Metrics

| Metric | Current State | Target |
|--------|--------------|--------|
| Weekly time spent on data collection | 3-5 hours (estimated) | < 30 minutes (review only) |
| Data entry errors | Unknown (manual risk) | < 2% (AI + validation + review) |
| Time to competitive insight | Days (manual Excel analysis) | Minutes (dashboard queries) |
| Retailers monitored | 5 | 7 (easily extensible) |
| Historical data accessibility | Slow Excel filtering | Instant database queries with visualization |
| Report generation time | 1-2 hours (manual PowerPoint) | < 1 minute (automated export) |

---

## 13. Design Decisions (Resolved)

The following questions were discussed and resolved during planning:

### 1. AI Model Strategy
**Decision:** Start with Claude Sonnet across all retailers, then optimize later.

Launch with Sonnet for consistent, high-accuracy extraction across all 7 retailers. After accumulating accuracy data over several scrape cycles, evaluate whether Haiku is sufficient for simpler retailer pages (e.g., Costco with fewer SKUs, Memory Express with clean layouts) to reduce API costs. The extraction pipeline should be designed with a configurable model parameter per-retailer to make this switch trivial.

### 2. Historical Data Normalization
**Decision:** Normalize all vendor names during import, with an audit log.

During the Excel-to-SQLite import, all vendor names will be standardized to canonical forms (e.g., "ACER" and "Acer" both become "Acer"; "Asus" and "ASUS" both become "ASUS"). A separate `import_audit_log` table will record every normalization change with the original value, normalized value, and the row reference, so the transformation is fully traceable and reversible if needed.

**Canonical Vendor Names:** Acer, Apple, ASUS, Dell, Gigabyte, HP, Huawei, LG, Lenovo, Microsoft, MSI, Samsung

### 3. Promotion Cycle Management
**Decision:** Auto-detect with manual override.

The system will auto-assign promotional cycles based on configurable date ranges:

| Cycle | Approximate Date Range |
|-------|----------------------|
| Spring (SPR) | January – April |
| Back-to-School (BTS) | May – August |
| Holiday (HOL) | September – December |

During the human review step, the suggested cycle label will be shown and editable. The reviewer can override the auto-assignment for edge cases (e.g., a late-December promotion that belongs to the next year's Spring cycle). Cycle date boundaries are configurable in Settings.

### 4. Screenshot Storage
**Decision:** Keep everything at full resolution indefinitely.

All screenshots will be stored at full resolution with no automatic compression or archival. Disk storage is inexpensive, and the visual archive has long-term strategic value for tracking how retailers change their promotional presentation over time. Estimated storage: approximately 2-5 MB per retailer per week, or roughly 2-4 GB per year for all 7 retailers — manageable on any modern system.

### 5. Notification Method
**Decision:** Email digest plus immediate critical alerts.

The alert system will support two email notification channels:

- **Weekly digest email** — Sent after the scheduled Monday scrape completes and data is reviewed. Summarizes all new promotions, ended deals, and notable changes across all retailers. Formatted as a clean HTML email with key stats and links back to the dashboard for deeper analysis.
- **Critical alert emails** — Sent immediately when a critical-severity alert is triggered (e.g., deep discount anomaly, a competitor launching a promotion that directly targets your product line). These are time-sensitive and shouldn't wait for the weekly digest.

Email delivery will use SMTP configuration (configurable in Settings — works with Gmail, Outlook, or any SMTP provider). Dashboard alerts remain the primary notification surface, with email as a supplementary channel.
