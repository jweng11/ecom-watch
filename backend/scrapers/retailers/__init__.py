"""Retailer-specific scraper implementations."""

from scrapers.retailers.bestbuy import BestBuyScraper
from scrapers.retailers.staples import StaplesScraper
from scrapers.retailers.walmart import WalmartScraper
from scrapers.retailers.costco import CostcoScraper
from scrapers.retailers.amazon import AmazonScraper
from scrapers.retailers.canadacomputers import CanadaComputersScraper
from scrapers.retailers.memoryexpress import MemoryExpressScraper
from scrapers.retailers.thesource import TheSourceScraper

SCRAPER_REGISTRY = {
    "bestbuy": BestBuyScraper,
    "staples": StaplesScraper,
    "walmart": WalmartScraper,
    "costco": CostcoScraper,
    "amazon": AmazonScraper,
    "canadacomputers": CanadaComputersScraper,
    "memoryexpress": MemoryExpressScraper,
    "thesource": TheSourceScraper,
}

__all__ = [
    "SCRAPER_REGISTRY",
    "BestBuyScraper",
    "StaplesScraper",
    "WalmartScraper",
    "CostcoScraper",
    "AmazonScraper",
    "CanadaComputersScraper",
    "MemoryExpressScraper",
    "TheSourceScraper",
]
