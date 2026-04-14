import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
API_TITLE = os.getenv("API_TITLE", "Specialist Recommender API")
API_VERSION = os.getenv("API_VERSION", "0.2.0")
API_DESCRIPTION = os.getenv(
    "API_DESCRIPTION",
    "AI-assisted triage API for specialist consultation booking.",
)
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
]

# Primary model from .env, with fallbacks if it rate-limits or 404s
PRIMARY_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-3n-e4b-it:free")

FREE_MODEL_FALLBACKS = [
    PRIMARY_MODEL,
    # Mistral family
    "mistralai/mistral-7b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    # Meta Llama family
    "meta-llama/llama-3.1-8b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    # DeepSeek
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat-v3-0324:free",
    # Google
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    # Qwen
    "qwen/qwen3-8b:free",
    "qwen/qwen-2.5-7b-instruct:free",
]
# Deduplicate while preserving order
seen = set()
FREE_MODEL_FALLBACKS = [
    m for m in FREE_MODEL_FALLBACKS if not (m in seen or seen.add(m))
]
