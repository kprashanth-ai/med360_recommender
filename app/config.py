import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI (primary)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# OpenRouter (fallback)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Mock mode (set MOCK_MODE=true to return a static response without calling any LLM)
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# API metadata
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

# OpenRouter fallback chain (used only if OpenAI fails)
OPENROUTER_FALLBACKS = [
    "mistralai/mistral-7b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "qwen/qwen3-8b:free",
    "qwen/qwen-2.5-7b-instruct:free",
]
