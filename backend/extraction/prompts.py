"""Prompt templates for AI extraction."""

SYSTEM_PROMPT = """You are a data extraction specialist. Your task is to extract laptop promotion/deal data from retailer webpage HTML.

For each laptop product on the page that has a sale/promotion price, extract the following fields:

- vendor: Brand name (e.g., Acer, ASUS, Dell, HP, Lenovo, MSI, Apple, Samsung, etc.)
- sku: Product name/model as shown on the page
- msrp: Regular/original price in CAD (number only, no $ sign)
- ad_price: Sale/advertised price in CAD (number only, no $ sign)
- discount: Dollar amount saved (msrp - ad_price)
- discount_pct: Percentage discount (0-100)
- form_factor: "Laptop", "2-in-1", "Chromebook", "Gaming Laptop", etc.
- lcd_size: Screen size (e.g., "15.6\"", "14\"")
- resolution: Screen resolution if available (e.g., "1920x1080", "FHD", "4K")
- touch: "Yes" or "No" if mentioned, null otherwise
- os: Operating system (e.g., "Windows 11 Home", "ChromeOS")
- cpu: Processor (e.g., "Intel Core i7-13700H", "AMD Ryzen 5 7530U")
- gpu: Graphics card if mentioned (e.g., "NVIDIA RTX 4060", "Intel Iris Xe")
- ram: Memory (e.g., "16GB", "8GB DDR5")
- storage: Storage (e.g., "512GB SSD", "1TB NVMe")
- notes: Any other notable features or promo details
- promo_type: Type of promotion (e.g., "Sale", "Clearance", "Bundle", "Open Box")
- source_url: Product URL if available in the HTML

IMPORTANT RULES:
1. Only extract products that have BOTH a regular price and a sale/promotional price (i.e., products on sale).
2. If a product has no discount, skip it.
3. Extract ALL on-sale laptops/notebooks on the page.
4. Return a JSON array of objects. If no promotions found, return an empty array [].
5. Be precise with prices — extract exact dollar amounts.
6. For specs, extract exactly what's shown; don't guess or infer.
"""

# Retailer-specific extraction guidance
RETAILER_GUIDANCE = {
    "canadacomputers": """RETAILER: Canada Computers (canadacomputers.com)
- Product cards show the product name, specs in a condensed format, regular price (crossed out), and sale price.
- The "SAVE $X" or savings amount is often shown explicitly.
- Product URLs follow the pattern: /product/PRODUCT_ID
- Specs are typically listed as bullet points or in the product title (e.g., "15.6\" FHD IPS / i7-13700H / 16GB / 512GB SSD")
- Look for elements with classes like 'productTemplate_price', 'line-through' (regular price), sale price styling.
- Some products may be "Open Box" or "Refurbished" — note this in promo_type.
""",

    "bestbuy": """RETAILER: Best Buy Canada (bestbuy.ca)
- Products show regular and sale prices with "Save $X" badges.
- Specs are in the product title and feature bullets.
- PLACEHOLDER — update when scraping is enabled.
""",

    "amazon": """RETAILER: Amazon.ca
- Prices shown as "Was: $X" and current price.
- PLACEHOLDER — update when scraping is enabled.
""",

    "walmart": """RETAILER: Walmart Canada
- PLACEHOLDER — update when scraping is enabled.
""",

    "thesource": """RETAILER: The Source
- PLACEHOLDER — update when scraping is enabled.
""",

    "costco": """RETAILER: Costco Canada
- PLACEHOLDER — update when scraping is enabled.
""",

    "memoryexpress": """RETAILER: Memory Express
- PLACEHOLDER — update when scraping is enabled.
""",

    "staples": """RETAILER: Staples Canada
- PLACEHOLDER — update when scraping is enabled.
""",
}

FEW_SHOT_EXAMPLES = """
Here are examples of correctly extracted promotions:

Example 1:
{
  "vendor": "ASUS",
  "sku": "ASUS Vivobook 15 OLED - 15.6\" FHD OLED / i5-13500H / 16GB / 512GB SSD",
  "msrp": 899.99,
  "ad_price": 699.99,
  "discount": 200.00,
  "discount_pct": 22.2,
  "form_factor": "Laptop",
  "lcd_size": "15.6\"",
  "resolution": "FHD OLED",
  "touch": null,
  "os": "Windows 11 Home",
  "cpu": "Intel Core i5-13500H",
  "gpu": null,
  "ram": "16GB",
  "storage": "512GB SSD",
  "notes": null,
  "promo_type": "Sale",
  "source_url": null
}

Example 2:
{
  "vendor": "Lenovo",
  "sku": "Lenovo IdeaPad Slim 3 - 15.6\" FHD / Ryzen 5 7530U / 8GB / 256GB SSD",
  "msrp": 699.99,
  "ad_price": 499.99,
  "discount": 200.00,
  "discount_pct": 28.6,
  "form_factor": "Laptop",
  "lcd_size": "15.6\"",
  "resolution": "FHD",
  "touch": "No",
  "os": "Windows 11 Home",
  "cpu": "AMD Ryzen 5 7530U",
  "gpu": "AMD Radeon Graphics",
  "ram": "8GB",
  "storage": "256GB SSD",
  "notes": null,
  "promo_type": "Sale",
  "source_url": null
}

Example 3:
{
  "vendor": "HP",
  "sku": "HP Pavilion 14 Gaming Laptop - 14\" FHD 144Hz / i7-13700H / 16GB DDR5 / 512GB / RTX 4050",
  "msrp": 1399.99,
  "ad_price": 1099.99,
  "discount": 300.00,
  "discount_pct": 21.4,
  "form_factor": "Gaming Laptop",
  "lcd_size": "14\"",
  "resolution": "FHD 144Hz",
  "touch": "No",
  "os": "Windows 11 Home",
  "cpu": "Intel Core i7-13700H",
  "gpu": "NVIDIA RTX 4050",
  "ram": "16GB DDR5",
  "storage": "512GB SSD",
  "notes": null,
  "promo_type": "Sale",
  "source_url": null
}
"""


def build_extraction_prompt(retailer_slug: str, html_content: str) -> str:
    """Build the full extraction prompt for a given retailer and HTML content."""
    guidance = RETAILER_GUIDANCE.get(retailer_slug, "")

    # Truncate HTML if too large (Gemini context limit)
    max_html_chars = 900_000  # ~900KB, leave room for prompt
    if len(html_content) > max_html_chars:
        html_content = html_content[:max_html_chars] + "\n... [HTML TRUNCATED]"

    return f"""{guidance}

{FEW_SHOT_EXAMPLES}

Now extract all laptop promotions from the following HTML. Return ONLY a JSON array of promotion objects (no markdown, no explanation):

<html>
{html_content}
</html>"""
