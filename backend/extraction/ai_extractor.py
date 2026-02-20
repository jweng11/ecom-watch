"""Gemini-based AI extraction of promotion data from retailer HTML."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

from google import genai

from extraction.schema import ExtractedPromotion, ExtractionResult
from extraction.prompts import SYSTEM_PROMPT, build_extraction_prompt

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.0-flash"
MAX_RETRIES = 2


def _get_client() -> genai.Client:
    """Create a Gemini client from env var."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)


def _parse_json_response(text: str) -> list[dict]:
    """Parse JSON array from Gemini response, handling markdown fences."""
    text = text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        # Remove first line (```json or ```) and last line (```)
        lines = text.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    data = json.loads(text)
    if isinstance(data, dict) and "promotions" in data:
        data = data["promotions"]
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")
    return data


async def extract_promotions(
    html_content: str,
    retailer_slug: str,
    retailer_name: str,
) -> ExtractionResult:
    """
    Extract promotions from HTML using Gemini.

    Args:
        html_content: Raw HTML of the retailer's laptop/deals page
        retailer_slug: e.g., "canadacomputers"
        retailer_name: e.g., "Canada Computers"

    Returns:
        ExtractionResult with extracted promotions
    """
    start_time = time.time()

    try:
        client = _get_client()
    except RuntimeError as e:
        return ExtractionResult(
            retailer=retailer_name,
            error=str(e),
            extraction_time=time.time() - start_time,
        )

    user_prompt = build_extraction_prompt(retailer_slug, html_content)

    last_error: Optional[str] = None
    raw_response: Optional[str] = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            logger.info(
                f"[{retailer_slug}] Gemini extraction attempt {attempt + 1}/{MAX_RETRIES + 1}"
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    {"role": "user", "parts": [{"text": user_prompt}]},
                ],
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "temperature": 0.1,
                    "response_mime_type": "application/json",
                },
            )

            raw_response = response.text
            items = _parse_json_response(raw_response)

            promotions = []
            for item in items:
                try:
                    item["retailer"] = retailer_name
                    promo = ExtractedPromotion(**item)
                    promotions.append(promo)
                except Exception as e:
                    logger.warning(f"[{retailer_slug}] Failed to parse item: {e}")

            extraction_time = time.time() - start_time
            logger.info(
                f"[{retailer_slug}] Extracted {len(promotions)} promotions in {extraction_time:.1f}s"
            )

            return ExtractionResult(
                retailer=retailer_name,
                promotions=promotions,
                extraction_time=extraction_time,
                model_used=MODEL_NAME,
                raw_response=raw_response,
            )

        except json.JSONDecodeError as e:
            last_error = f"JSON parse error: {e}"
            logger.warning(f"[{retailer_slug}] {last_error} (attempt {attempt + 1})")
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning(f"[{retailer_slug}] {last_error} (attempt {attempt + 1})")

    extraction_time = time.time() - start_time
    return ExtractionResult(
        retailer=retailer_name,
        error=f"All {MAX_RETRIES + 1} attempts failed. Last error: {last_error}",
        extraction_time=extraction_time,
        model_used=MODEL_NAME,
        raw_response=raw_response,
    )
