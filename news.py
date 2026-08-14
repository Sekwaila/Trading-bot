"""
SEKWAILA OMEGA X — NEWS INTELLIGENCE

Fetch headlines via NewsAPI (optional) and provide a cached summary using ai_provider
if configured. Non-blocking TTL cache to avoid excessive external calls on Streamlit reruns.
"""

import os
import requests
from typing import List, Tuple, Dict, Any

from config import ASSETS
from cache import ttl_cache
from ai_provider import summarize_headlines
from logger import get_logger

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "").strip()
NEWSAPI_URL = "https://newsapi.org/v2/everything"
NEWS_TTL_SECONDS = int(os.getenv("NEWS_TTL_SECONDS", "900"))  # 15 minutes default

logger = get_logger("NEWS")


def _build_search_query(symbol: str) -> str:
    """Constructs a clean search query for NewsAPI tailored to financial tickers."""
    ticker_name = ASSETS.get(symbol, "")
    clean_symbol = symbol.replace("/", "").upper()

    # Asset-specific mappings for cleaner news queries
    query_map = {
        "XAUUSD": "Gold price OR Gold spot OR XAUUSD",
        "BTCUSD": "Bitcoin OR Crypto market OR BTCUSD",
        "EURUSD": "EURUSD OR Euro US Dollar OR Forex ECB",
        "GBPUSD": "GBPUSD OR Pound Dollar OR Bank of England",
        "USDJPY": "USDJPY OR Dollar Yen OR Bank of Japan",
        "NAS100": "Nasdaq 100 OR Tech stocks OR US100",
        "US30": "Dow Jones OR Wall Street OR US30",
    }

    if clean_symbol in query_map:
        return query_map[clean_symbol]

    if ticker_name and ticker_name != symbol:
        return f'"{symbol}" OR "{ticker_name}"'

    return f'"{symbol}"'


@ttl_cache(ttl=NEWS_TTL_SECONDS)
def fetch_news_for_asset(symbol: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Return a list of headline strings and raw article dicts for the given symbol.
    If NEWSAPI_KEY is not set or request fails, return empty lists.
    """
    if not symbol:
        return [], []

    if not NEWSAPI_KEY:
        logger.debug("NEWSAPI_KEY not set; returning empty news for %s", symbol)
        return [], []

    query = _build_search_query(symbol)
    params = {
        "q": query,
        "pageSize": 15,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWSAPI_KEY,
    }

    try:
        resp = requests.get(NEWSAPI_URL, params=params, timeout=8)

        if resp.status_code != 200:
            logger.warning(
                "NewsAPI returned HTTP %s for %s: %s",
                resp.status_code,
                symbol,
                resp.text[:200]
            )
            return [], []

        data = resp.json()
        articles = data.get("articles", [])[:12]

        headlines = []
        clean_articles = []

        for a in articles:
            title = a.get("title")
            if not title or title == "[Removed]":
                continue

            source_name = a.get("source", {}).get("name", "Market News")
            headlines.append(f"{source_name} — {title}")
            clean_articles.append(a)

        return headlines, clean_articles

    except Exception as exc:
        logger.warning("News fetch failed for %s: %s", symbol, exc)
        return [], []


def summarise_headlines(headlines: List[str]) -> str:
    """Return an LLM summary when possible, otherwise a simple bullet list."""
    if not headlines:
        return "No recent market headlines found or NEWSAPI_KEY is missing."

    try:
        return summarize_headlines(headlines)
    except Exception as exc:
        logger.warning("Headline summarisation failed: %s", exc)
        return "\n".join([f"- {h}" for h in headlines[:5]])
