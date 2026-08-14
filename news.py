"""
SEKWAILA OMEGA X — NEWS INTELLIGENCE

Fetch headlines via NewsAPI (optional) and provide a cached summary using ai_provider
if configured. Non-blocking TTL cache to avoid excessive external calls on Streamlit reruns.
"""

import os
import time
import requests
from typing import List, Tuple

from config import ASSETS
from cache import ttl_cache
from ai_provider import summarize_headlines
from logger import get_logger

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSAPI_URL = "https://newsapi.org/v2/everything"
NEWS_TTL_SECONDS = int(os.getenv("NEWS_TTL_SECONDS", "900"))  # 15 minutes

logger = get_logger("NEWS")


@ttl_cache(ttl=NEWS_TTL_SECONDS)
def fetch_news_for_asset(symbol: str) -> Tuple[List[str], List[dict]]:
    """Return a list of headline strings and raw article dicts for the given symbol.
    If NEWSAPI_KEY is not set, return an empty list.
    """
    ticker = ASSETS.get(symbol)
    if not NEWSAPI_KEY:
        logger.debug("NEWSAPI_KEY not set; returning empty news for %s", symbol)
        return [], []
    if not ticker:
        return [], []

    q = f"{symbol} OR {ticker}"
    params = {
        "q": q,
        "pageSize": 20,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWSAPI_KEY,
    }
    try:
        resp = requests.get(NEWSAPI_URL, params=params, timeout=8)
        if resp.status_code != 200:
            logger.warning("NewsAPI returned %s: %s", resp.status_code, resp.text[:200])
            return [], []
        data = resp.json()
        articles = data.get("articles", [])[:12]
        headlines = [f"{a.get('source',{}).get('name','')} - {a.get('title')}" for a in articles]
        return headlines, articles
    except Exception as exc:
        logger.warning("News fetch failed for %s: %s", symbol, exc)
        return [], []


def summarise_headlines(headlines: List[str]) -> str:
    """Return an LLM summary when possible, otherwise a simple bullet list."""
    if not headlines:
        return "No recent headlines or NEWSAPI_KEY not configured."
    try:
        return summarize_headlines(headlines)
    except Exception as exc:
        logger.warning("Headline summarisation failed: %s", exc)
        return "\n".join([f"- {h}" for h in headlines[:5]])
