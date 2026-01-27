# Laptop Promotion Tracker

A simple tool that scrapes laptop deals from major retailers, takes screenshots, and uses an LLM to intelligently extract and maintain promotion data in Excel.

## Features

- Screenshots of promotion pages from Best Buy, Walmart, Target
- LLM-powered extraction of product names, prices, discounts, specs
- Auto-maintained Excel file with searchable/filterable data
- Summary statistics by retailer and brand

---

## Windows Setup (Recommended)

### Step 1: Install Python

Download and install Python from [python.org](https://www.python.org/downloads/). During installation, check "Add Python to PATH".

### Step 2: Run Setup Script

Double-click `setup_windows.bat` to install all dependencies.

### Step 3: Set Your API Key

1. Press `Windows + R`
2. Type: `rundll32 sysdm.cpl,EditEnvironmentVariables`
3. Under "User variables", click **New**
4. Variable name: `ANTHROPIC_API_KEY`
5. Variable value: `your-api-key-here`
6. Click OK

### Step 4: Run the Tracker

Double-click `run_tracker.bat`

### Step 5 (Optional): Schedule Weekly Runs

Right-click `schedule_weekly.bat` → **Run as administrator**

This creates a weekly task that runs every Sunday at 9:00 AM.

---

## Mac/Linux Setup

### 1. Install dependencies

```bash
cd promo_tracker
pip install -r requirements.txt
playwright install chromium
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Add to `~/.bashrc` or `~/.zshrc` to make permanent.

### 3. Run the tracker

```bash
python tracker.py
```

### 4. Schedule weekly (optional)

```bash
crontab -e
# Add this line for every Sunday at 9am:
0 9 * * 0 cd /path/to/promo_tracker && python3 tracker.py
```

---

## Output

All output goes to your Documents folder:

**Windows:** `C:\Users\YourName\Documents\laptop_promo_tracker\`
**Mac/Linux:** `~/Documents/laptop_promo_tracker/`

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
| Screenshot | Path to screenshot file |
| Source URL | Original page URL |

## Usage Options

```bash
# Full run: scrape + analyze
python tracker.py

# Only scrape (no LLM costs)
python tracker.py --scrape

# Only analyze existing screenshots
python tracker.py --analyze
```

## Using OpenAI Instead of Anthropic

1. Set your OpenAI API key:
   - **Windows:** Add `OPENAI_API_KEY` in Environment Variables
   - **Mac/Linux:** `export OPENAI_API_KEY="your-key-here"`

2. Edit `config.py` and change:
   ```python
   LLM_PROVIDER = "openai"
   ```

## Customization

Edit `config.py` to:
- Add/remove retailer URLs in the `SITES` list
- Change output directory
- Switch LLM provider
- Adjust browser viewport and timeouts

## Cost Estimate

Using Claude Sonnet with 3 retailer screenshots per week:
- ~$0.10-0.30 per run (depending on screenshot sizes)
- ~$1-2 per month for weekly runs

## Troubleshooting

**"ANTHROPIC_API_KEY not set" error:**
- Make sure you set the environment variable and restarted your terminal/command prompt

**Screenshots are blank or show errors:**
- Some retailers may block automated browsers
- Try increasing `PAGE_LOAD_WAIT_MS` in config.py
- Run manually to see what's happening: `python tracker.py --scrape`

**Excel file won't open:**
- Make sure it's not already open in Excel
- Check the Documents folder for the file
