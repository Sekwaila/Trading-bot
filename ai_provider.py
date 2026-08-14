"""
SEKWAILA OMEGA X — AI provider wrapper

Supports OpenAI Chat Completions (v1.x/v2.x SDK). If OPENAI_API_KEY is not set or OpenAI 
fails, the module provides a lightweight local summariser fallback.
"""
import os
from typing import List, Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Initialize Client safely for OpenAI v1.0+ SDK
_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        _client = None


def _local_summarize_signal(result: Dict[str, Any]) -> str:
    """Minimal local summariser if no LLM key or client is available."""
    bias = result.get("bias", "NEUTRAL")
    score = result.get("score", "N/A")
    entry = result.get("entry_price") or result.get("entry", "N/A")
    stop = result.get("stop_loss") or result.get("stop", "N/A")
    tp1 = result.get("tp1", "N/A")
    structure = result.get("structure", "N/A")
    reason = result.get("reason", "")
    
    lines = [
        f"⚡ Signal: {bias} (Score: {score}%)",
        f"📐 Structure: {structure}"
    ]
    if bias in ("BUY", "SELL"):
        lines.append(f"🎯 Entry: {entry} | Stop: {stop} | TP1: {tp1}")
    if reason:
        lines.append(f"📝 Rationale: {reason}")
        
    return "\n".join(lines)


def summarize_signal(
    result: Dict[str, Any], 
    max_tokens: int = 300, 
    model: str = "gpt-3.5-turbo"
) -> str:
    """Return a short natural-language narrative for an engine result.

    If OPENAI_API_KEY is active and client is ready, calls OpenAI; otherwise 
    falls back to a local summary.
    """
    if not _client:
        return _local_summarize_signal(result)

    try:
        system_instruction = (
            "You are SEKWAILA OMEGA X AI, a concise and objective trading assistant. "
            "Given a structured Smart Money Concepts (SMC) signal, write a brief (3-5 sentence) "
            "narrative covering the directional bias, key level targets (entry/SL/TP), "
            "and market rationale. Avoid financial advice terminology."
        )
        prompt = f"Signal Data:\n{result}\n\nProvide market summary:"

        response = _client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        
        narrative = response.choices[0].message.content.strip()
        return narrative

    except Exception as exc:
        # Fallback to local summary on network, key, or runtime errors
        local_sum = _local_summarize_signal(result)
        return f"{local_sum}\n\n⚠️ (LLM Narrative Unavailable: {exc})"


def summarize_headlines(
    headlines: List[str], 
    max_tokens: int = 200, 
    model: str = "gpt-3.5-turbo"
) -> str:
    """Summarize a list of market headlines into actionable bullet points.
    Falls back to raw bullet list if no key is present.
    """
    if not headlines:
        return "No recent news headlines available."

    if not _client:
        return "\n".join([f"- {h}" for h in headlines[:5]])

    try:
        system_instruction = (
            "You are a quick-brief financial news analyst. Given headlines, "
            "produce 3 concise bullet points outlining key drivers and market impact."
        )
        joined_headlines = "\n".join([f"- {h}" for h in headlines[:12]])
        prompt = f"Headlines:\n{joined_headlines}\n\nProvide 3 key bullet points:"

        response = _client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    except Exception as exc:
        return "\n".join([f"- {h}" for h in headlines[:5]]) + f"\n\n⚠️ (LLM Error: {exc})"
