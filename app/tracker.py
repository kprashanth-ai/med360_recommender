"""
Usage and cost tracker for OpenRouter / OpenAI calls.
Reads rate-limit headers and token counts per response,
calculates cost from a pricing table, and appends to logs/usage.json.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Price per 1M tokens (input / output) in USD
# Free models = $0. Add paid models as you upgrade.
MODEL_PRICING: dict[str, dict[str, float]] = {
    # --- Free (OpenRouter) ---
    "google/gemma-3n-e4b-it:free":              {"input": 0.0, "output": 0.0},
    "google/gemma-3-27b-it:free":               {"input": 0.0, "output": 0.0},
    "mistralai/mistral-7b-instruct:free":       {"input": 0.0, "output": 0.0},
    "meta-llama/llama-3.1-8b-instruct:free":    {"input": 0.0, "output": 0.0},
    "deepseek/deepseek-r1:free":                {"input": 0.0, "output": 0.0},
    # --- Paid (OpenAI via OpenRouter or direct) ---
    "openai/gpt-4o-mini":                       {"input": 0.15,  "output": 0.60},
    "openai/gpt-4o":                            {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":                              {"input": 0.15,  "output": 0.60},
    "gpt-4o":                                   {"input": 2.50,  "output": 10.00},
}

LOG_PATH = Path(__file__).parent.parent / "logs" / "usage.json"


def _load_log() -> list:
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_log(entries: list) -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    LOG_PATH.write_text(json.dumps(entries, indent=2))


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    return (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1_000_000


def parse_rate_limits(headers: dict) -> dict:
    """
    Extract rate-limit fields from OpenRouter response headers.
    OpenRouter sends both request-count limits and token limits.
    Headers (lowercase after httpx normalisation):
      x-ratelimit-limit / x-ratelimit-remaining / x-ratelimit-reset
      x-ratelimit-limit-requests / x-ratelimit-remaining-requests
      x-ratelimit-limit-tokens   / x-ratelimit-remaining-tokens
      x-ratelimit-reset-requests / x-ratelimit-reset-tokens
    """
    def safe_int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def fmt_reset(ms_val):
        ms = safe_int(ms_val)
        if ms:
            return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return None

    # Requests quota (primary limit OpenRouter enforces for free tier)
    req_limit     = safe_int(headers.get("x-ratelimit-limit-requests")
                             or headers.get("x-ratelimit-limit"))
    req_remaining = safe_int(headers.get("x-ratelimit-remaining-requests")
                             or headers.get("x-ratelimit-remaining"))
    req_reset     = fmt_reset(headers.get("x-ratelimit-reset-requests")
                              or headers.get("x-ratelimit-reset"))

    # Token quota (may not be present on all free models)
    tok_limit     = safe_int(headers.get("x-ratelimit-limit-tokens"))
    tok_remaining = safe_int(headers.get("x-ratelimit-remaining-tokens"))
    tok_reset     = fmt_reset(headers.get("x-ratelimit-reset-tokens"))

    return {
        "requests": {
            "limit":     req_limit,
            "remaining": req_remaining,
            "reset":     req_reset,
        },
        "tokens": {
            "limit":     tok_limit,
            "remaining": tok_remaining,
            "reset":     tok_reset,
        },
    }


def record_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    rate_limits: dict,
) -> dict:
    """Build a usage entry, append to log file, and return it."""
    cost = calculate_cost(model, prompt_tokens, completion_tokens)
    entry = {
        "timestamp":         datetime.now(tz=timezone.utc).isoformat(),
        "model":             model,
        "prompt_tokens":     prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens":      prompt_tokens + completion_tokens,
        "cost_usd":          round(cost, 8),
        "rate_limits":       rate_limits,
    }
    entries = _load_log()
    entries.append(entry)
    _save_log(entries)
    return entry


def get_session_totals() -> dict:
    """Aggregate totals across all logged entries."""
    entries = _load_log()
    if not entries:
        return {"total_requests": 0, "total_tokens": 0, "total_cost_usd": 0.0}
    return {
        "total_requests":    len(entries),
        "total_tokens":      sum(e.get("total_tokens", 0) for e in entries),
        "total_cost_usd":    round(sum(e.get("cost_usd", 0) for e in entries), 8),
    }
