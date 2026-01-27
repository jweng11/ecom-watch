"""
LLM-powered analysis of promotion screenshots.
Extracts structured data from screenshots using vision capabilities.
"""
import base64
import json
from pathlib import Path


def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


EXTRACTION_PROMPT = """Analyze this screenshot of a laptop promotions/deals page from {retailer}.

Extract ALL visible laptop promotions and deals. For each promotion found, extract:
- product_name: Full laptop name/model
- brand: Manufacturer (Dell, HP, Lenovo, Apple, ASUS, Acer, etc.)
- original_price: Original/list price (if shown)
- sale_price: Current/sale price
- discount_amount: Dollar amount saved (if shown)
- discount_percent: Percentage off (if shown)
- promo_type: Type of deal (e.g., "Sale", "Clearance", "Member Deal", "Limited Time", "Doorbuster")
- key_specs: Brief specs if visible (RAM, storage, processor, screen size)
- promo_end_date: When deal expires (if shown)

Return a JSON array of promotions. If no promotions are clearly visible, return an empty array.
Only include items you can clearly see - do not guess or fabricate data.

Example format:
[
  {{
    "product_name": "HP Pavilion 15.6\" Laptop",
    "brand": "HP",
    "original_price": "$699.99",
    "sale_price": "$549.99",
    "discount_amount": "$150",
    "discount_percent": "21%",
    "promo_type": "Sale",
    "key_specs": "Intel Core i5, 16GB RAM, 512GB SSD",
    "promo_end_date": null
  }}
]

Return ONLY valid JSON, no other text."""


def analyze_with_anthropic(image_path: str, retailer: str, api_key: str) -> list[dict]:
    """Use Claude to analyze screenshot and extract promotions."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    image_data = encode_image_to_base64(image_path)

    # Determine media type from file extension
    ext = Path(image_path).suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT.format(retailer=retailer)
                    }
                ],
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Parse JSON from response
    try:
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        return json.loads(response_text)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse LLM response as JSON: {response_text[:200]}")
        return []


def analyze_with_openai(image_path: str, retailer: str, api_key: str) -> list[dict]:
    """Use GPT-4 Vision to analyze screenshot and extract promotions."""
    import openai

    client = openai.OpenAI(api_key=api_key)
    image_data = encode_image_to_base64(image_path)

    ext = Path(image_path).suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT.format(retailer=retailer)
                    }
                ],
            }
        ],
    )

    response_text = response.choices[0].message.content.strip()

    try:
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        return json.loads(response_text)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse LLM response as JSON: {response_text[:200]}")
        return []


def analyze_screenshot(image_path: str, retailer: str, provider: str, api_key: str) -> list[dict]:
    """
    Analyze a screenshot and extract promotion data.

    Args:
        image_path: Path to screenshot image
        retailer: Name of retailer (for context)
        provider: "anthropic" or "openai"
        api_key: API key for the provider

    Returns:
        List of promotion dictionaries
    """
    if provider == "anthropic":
        return analyze_with_anthropic(image_path, retailer, api_key)
    elif provider == "openai":
        return analyze_with_openai(image_path, retailer, api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
