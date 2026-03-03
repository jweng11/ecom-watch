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
- lcd_size: Screen size (e.g., "15.6\\"", "14\\"")
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
PAGE STRUCTURE:
- Deals page at /specials.php?cat=Laptops/Netbooks or category pages under /en/91/laptops-tablet
- Product cards use div.productTemplate or similar grid layout.
- Each card contains: product image, product title (with embedded specs like "15.6\\" FHD IPS / i7-13700H / 16GB / 512GB SSD"), pricing block.
- Regular price appears with strikethrough/line-through styling (class like 'productTemplate_price' or text-decoration:line-through).
- Sale price is displayed prominently, often in red or with a "SAVE $X" badge nearby.
- Product URLs are relative: /product/PRODUCT_ID or /en/product/...
- "Open Box" and "Refurbished" items have distinct badges — capture in promo_type.
- Some items show "Clearance" or "Limited Time" tags.
- Specs may be in bullet points below the title or encoded in the product name string.
""",

    "bestbuy": """RETAILER: Best Buy Canada (bestbuy.ca)
PAGE STRUCTURE:
- Laptop deals at /en-ca/collection/laptops-on-sale/46082 or /en-ca/collection/windows-laptops-on-sale/66056
- Product listing uses a grid of product cards (div with data-testid or class containing 'productListItem').
- Each card shows: product image, product title, star rating, pricing block.
- Regular price shown with strikethrough; sale price in bold/prominent red text.
- "Save $X" or "Save X%" badge often appears next to or below the pricing.
- Open Box deals on a separate page (/en-ca/collection/open-box/16073) — note as "Open Box" in promo_type.
- Product URLs follow: /en-ca/product/NAME/PRODUCT_ID
- Specs are embedded in the product title (e.g., "HP Pavilion 15.6\\" Laptop - Intel Core i7-1355U - 16GB RAM - 512GB SSD").
- Some cards show "Marketplace" seller — still extract if on sale.
""",

    "amazon": """RETAILER: Amazon.ca
PAGE STRUCTURE:
- Laptop deals at /s?rh=n:677252011,p_n_deal_type:23565506011 or /b?node=13895240011
- Product listings use div.s-result-item with data-asin attributes.
- Pricing shows "Was: $X" (strikethrough) and current price below.
- Some show "X% off" or "Save $X" badges in red.
- Product title is in an h2 > a > span element with full product name including specs.
- Product URLs: /dp/ASIN or /gp/product/ASIN
- "Limited time deal" badge in orange/yellow — note as "Limited Time Deal" in promo_type.
- "Lightning Deal" or "Deal of the Day" badges — capture in promo_type.
- Coupon discounts ("Save X% with coupon") should be noted in 'notes' but NOT reflected in ad_price unless explicitly shown as final price.
- Specs are in the product title string; parse brand, screen size, CPU, RAM, storage from the title.
""",

    "walmart": """RETAILER: Walmart Canada (walmart.ca)
PAGE STRUCTURE:
- Laptop category at /en/cp/electronics/laptops-computers-accessories/laptops/30548
- Product grid uses card components with product image, title, pricing, and rating.
- Price display: "Was $X" with strikethrough for regular price, current price prominently displayed.
- "Rollback" badge indicates a Walmart-specific sale (use promo_type "Rollback").
- "Clearance" items have distinct yellow/red badges.
- Product URLs: /en/ip/PRODUCT-NAME/PRODUCT_ID
- Product titles contain full specs (brand, screen size, processor, RAM, storage) in a long string.
- Some items are "Marketplace" (third-party sellers); still extract if discounted.
- "Save $X" text appears below the price block on some items.
""",

    "thesource": """RETAILER: The Source / Best Buy Express (thesource.ca)
PAGE STRUCTURE:
- Laptop listings at /en-ca/computers-tablets/laptops/c/scc-1-2
- Note: The Source is now Best Buy Express, sharing Best Buy Canada's catalog infrastructure.
- Product grid with cards showing: product image, title, pricing, badges.
- Regular price with strikethrough; sale price in bold.
- "Save $X" badge shown on sale items.
- Product URLs: /en-ca/product/NAME/PRODUCT_ID (similar to Best Buy)
- Product titles embed brand, screen size, and key specs.
- Smaller selection than Best Buy — focuses on mainstream and entry-level laptops.
- "Online Only" badges are common — note in 'notes' field.
""",

    "costco": """RETAILER: Costco Canada (costco.ca)
PAGE STRUCTURE:
- Laptop page at /laptops.html; deals at /computer-offers.html
- Product grid uses div.product-tile or similar tile layout.
- Costco typically shows a single "member price" — look for "After $X OFF" or "Instant Savings" badges that indicate a discount from the original price.
- Regular price may appear as "Manufacturer's Suggested Retail Price" or a crossed-out price.
- Sale/instant savings shown as "$X OFF" or "$X after instant savings".
- Product URLs: /PRODUCT-NAME.product.PRODUCT_ID.html
- Titles are descriptive: e.g., "Lenovo IdeaPad 3i 15.6\\" Laptop - Intel Core i5-1235U - 1080p - Windows 11"
- Costco bundles may include extras (mouse, bag) — note in 'notes'.
- Membership pricing is the norm; warehouse-only deals may not appear online.
""",

    "memoryexpress": """RETAILER: Memory Express (memoryexpress.com)
PAGE STRUCTURE:
- Laptop listings under /Category/Laptops-Notebooks and deals at /Promos/LimitedQuantity.cm.aspx
- Clearance page at /clearance with Open Box, Discontinued, Refurbished items.
- Product cards show: product image, title, price block with "Regular Price" and "Sale Price" labels.
- Discount shown as "You Save: $X (X%)" explicitly.
- Product URLs: /Products/ProductDetail?pid=PRODUCT_ID or descriptive slug paths.
- "Open Box" items have distinct orange badges — use promo_type "Open Box".
- "Limited Quantity" deals are time-limited; note in promo_type.
- Specs are typically in the product title and may also appear in a short description below.
- Memory Express uses a more technical audience format — CPU model numbers and GPU specs are usually explicit.
""",

    "staples": """RETAILER: Staples Canada (staples.ca)
PAGE STRUCTURE:
- Laptop page at /collections/laptops-90; deals at /collections/staples-deals-centre
- Product grid with tiles showing: product image, title, rating, pricing.
- Regular price shown with strikethrough; sale price below in bold/red.
- "SALE" badge overlay on product images for discounted items.
- "Save $X" or percentage discount shown near the price.
- Product URLs: /products/PRODUCT-NAME-PRODUCT_ID
- Product titles include brand and key specs; more detailed specs in product description (may not be visible in listing view).
- "Clearance" items marked separately — capture in promo_type.
- Staples offers business/education pricing — only extract the consumer sale price.
- Some items show "Online Only" or "In-Store Only" badges — note in 'notes'.
""",
}

FEW_SHOT_EXAMPLES = """
Here are examples of correctly extracted promotions:

Example 1:
{
  "vendor": "ASUS",
  "sku": "ASUS Vivobook 15 OLED - 15.6\\" FHD OLED / i5-13500H / 16GB / 512GB SSD",
  "msrp": 899.99,
  "ad_price": 699.99,
  "discount": 200.00,
  "discount_pct": 22.2,
  "form_factor": "Laptop",
  "lcd_size": "15.6\\"",
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
  "sku": "Lenovo IdeaPad Slim 3 - 15.6\\" FHD / Ryzen 5 7530U / 8GB / 256GB SSD",
  "msrp": 699.99,
  "ad_price": 499.99,
  "discount": 200.00,
  "discount_pct": 28.6,
  "form_factor": "Laptop",
  "lcd_size": "15.6\\"",
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
  "sku": "HP Pavilion 14 Gaming Laptop - 14\\" FHD 144Hz / i7-13700H / 16GB DDR5 / 512GB / RTX 4050",
  "msrp": 1399.99,
  "ad_price": 1099.99,
  "discount": 300.00,
  "discount_pct": 21.4,
  "form_factor": "Gaming Laptop",
  "lcd_size": "14\\"",
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
