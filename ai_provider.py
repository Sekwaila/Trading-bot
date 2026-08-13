"""
SEKWAILA OMEGA X — AI provider wrapper

Supports OpenAI (chat completions). If OPENAI_API_KEY is not set the
module provides a small local summariser fallback.
"""
import os
import time
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if OPENAI_API_KEY:
    import openai
    openai.api_key = OPENAI_API_KEY


def _local_summarize_signal(result: dict) -> str:
    # Minimal local summariser if no LLM key is provided
    bias = result.get("bias", "NEUTRAL")
    score = result.get("score")
    entry = result.get("entry")
    stop = result.get("stop")
    tp1 = result.get("tp1")
    structure = result.get("structure")
    reason = result.get("reason")
    lines = [f"Signal: {bias} (score={score})", f"Structure: {structure}"]
    if bias in ("BUY", "SELL"):
        lines.append(f"Entry: {entry} | Stop: {stop} | TP1: {tp1}")
    if reason:
        lines.append(f"Note: {reason}")
    return "\n".join(lines)


def summarize_signal(result: dict, max_tokens: int = 300, model: str = "gpt-3.5-turbo") -> str:
    """Return a short natural-language narrative for an engine result.

    If OPENAI_API_KEY is set, call OpenAI Chat Completions; otherwise fall back
    to a lightweight local summary.
    """
    if not OPENAI_API_KEY:
        return _local_summarize_signal(result)

    try:
        system = (
            "You are a concise trading assistant. Given a structured signal from a trading engine, "
            "produce a brief (3-6 sentence) human-readable narrative describing the bias, rationale, "
            "key levels (entry/stop/TP1), and a short risk note. Keep it factual and avoid advice language."
        )
        prompt = (
            f"Signal data:\n{result}\n\nWrite a concise summary:\n"
        )
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()
        return text
    except Exception as exc:
        # On failure, return local summary
        try:
            return _local_summarize_signal(result) + f"\n\n(LLM error: {exc})"
        except Exception:
            return "(Failed to summarise signal)"


def summarize_headlines(headlines: list[str], max_tokens: int = 200, model: str = "gpt-3.5-turbo") -> str:
    """Summarize a list of headlines into a short bullet summary using the LLM.
    Falls back to a simple join when no key is present.
    """
    if not OPENAI_API_KEY:
        return "\n".join([f"- {h}" for h in headlines[:5]])

    try:
        system = (
            "You are a concise news summariser for traders. Given a list of headlines and sources, "
            "produce a short (3-4 bullet) summary of market-relevant points and potential impacts."
        )
        joined = "\n".join([f"- {h}" for h in headlines[:12]])
        prompt = f"Headlines:\n{joined}\n\nProduce a 3-bullet market summary:" 
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return "\n".join([f"- {h}" for h in headlines[:5]]) + f"\n\n(LLM error: {exc})"
