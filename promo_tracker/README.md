# Laptop Promotion Tracker

A simple tool that scrapes laptop deals from major retailers, takes screenshots, and uses an LLM to intelligently extract and maintain promotion data in Excel.

## Features

- Screenshots of promotion pages from Best Buy, Walmart, Target
- LLM-powered extraction of product names, prices, discounts, specs
- Auto-maintained Excel file with searchable/filterable data
- Summary statistics by retailer and brand

## Quick Setup

### 1. Install dependencies

```bash
cd promo_tracker
pip install -r requirements.txt
playwright install chromium
```

### 2. Set your API key

**For Anthropic Claude (default):**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**For OpenAI:**
```bash
export OPENAI_API_KEY="your-key-here"
```
Then edit `config.py` and set `LLM_PROVIDER = "openai"`

### 3. Run the tracker

```bash
python tracker.py
```

## Output

All output goes to `~/Documents/laptop_promo_tracker/`:

```
laptop_promo_tracker/
├── laptop_promotions.xlsx    # Main Excel file with all data
└── screenshots/              # Full-page screenshots
    ├── bestbuy_laptops_2026-01-27_0900.png
    ├── walmart_laptops_2026-01-27_0900.png
    └── target_laptops_2026-01-27_0900.png
```

## Excel File Structure

| Column | Description |
|--------|-------------|
| Scrape Date | When the data was captured |
| Retailer | Best Buy, Walmart, or Target |
| Product Name | Full laptop name/model |
| Brand | Manufacturer |
| Original Price | List price |
| Sale Price | Current price |
| Discount $ | Amount saved |
| Discount % | Percentage off |
| Promo Type | Sale, Clearance, etc. |
| Key Specs | RAM, storage, processor |
| Promo Ends | Expiration date |
| Screenshot | Path to screenshot |
| Source URL | Page URL |

## Usage Options

```bash
# Full run: scrape + analyze
python tracker.py

# Only scrape (no LLM costs)
python tracker.py --scrape

# Only analyze existing screenshots
python tracker.py --analyze
```

## Schedule Weekly Runs

**Mac/Linux (cron):**
```bash
crontab -e
# Every Sunday at 9am:
0 9 * * 0 cd /path/to/promo_tracker && /usr/bin/python3 tracker.py
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Weekly
4. Action: Start Program
   - Program: `python`
   - Arguments: `C:\path\to\promo_tracker\tracker.py`
   - Start in: `C:\path\to\promo_tracker`

## Customization

Edit `config.py` to:
- Add/remove retailer URLs
- Change output directory
- Switch LLM provider
- Adjust browser settings

## Cost Estimate

Using Claude Sonnet with 3 retailer screenshots per week:
- ~$0.10-0.30 per run (depending on screenshot sizes)
- ~$1-2 per month for weekly runs
