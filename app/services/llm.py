import json

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)
from pydantic import ValidationError

from app.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_FALLBACKS,
)
from app.models import LLMRecommendationPayload
from app.prompts import SYSTEM_PROMPT
from app.tracker import parse_rate_limits, record_usage

openai_client = OpenAI(api_key=OPENAI_API_KEY)

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)


def _normalize_recommendation_payload(raw_content: str) -> dict:
    payload = json.loads(raw_content)
    validated = LLMRecommendationPayload.model_validate(payload)
    return validated.model_dump()


def _try_model(client: OpenAI, model: str, patient_info: str) -> tuple[dict, str, dict]:
    """
    Attempt a single model call. Returns (data, model, usage_entry) on success.
    Raises the original exception on failure so the caller can decide to continue or stop.
    """
    raw = client.with_raw_response.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Patient info: {patient_info}"},
        ],
        response_format={"type": "json_object"},
    )
    response = raw.parse()
    headers = dict(raw.headers)

    rate_limits = parse_rate_limits(headers)
    usage = response.usage
    usage_entry = record_usage(
        model=model,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        rate_limits=rate_limits,
    )

    message_content = response.choices[0].message.content or "{}"
    data = _normalize_recommendation_payload(message_content)
    return data, model, usage_entry


def get_recommendation(patient_info: str) -> tuple[dict, str, dict]:
    """
    Try OpenAI (primary) first, then iterate OpenRouter free models as fallback.
    Returns (response_dict, model_used, usage_entry).
    Raises RuntimeError if all providers fail.
    """
    failures: list[str] = []

    # --- Primary: OpenAI ---
    if OPENAI_API_KEY:
        try:
            print(f"  trying OpenAI/{OPENAI_MODEL} ...", flush=True)
            return _try_model(openai_client, OPENAI_MODEL, patient_info)
        except RateLimitError:
            failures.append(f"OpenAI/{OPENAI_MODEL} -> rate limited")
        except AuthenticationError:
            failures.append(f"OpenAI/{OPENAI_MODEL} -> authentication failed")
        except NotFoundError:
            failures.append(f"OpenAI/{OPENAI_MODEL} -> model not found")
        except (APIConnectionError, APITimeoutError):
            failures.append(f"OpenAI/{OPENAI_MODEL} -> connection or timeout error")
        except BadRequestError as e:
            failures.append(f"OpenAI/{OPENAI_MODEL} -> bad request ({e.status_code})")
        except APIError as e:
            failures.append(f"OpenAI/{OPENAI_MODEL} -> API error ({e.status_code})")
        except (json.JSONDecodeError, ValidationError):
            failures.append(f"OpenAI/{OPENAI_MODEL} -> invalid structured response")
        except Exception as e:
            failures.append(f"OpenAI/{OPENAI_MODEL} -> unexpected error ({type(e).__name__})")
    else:
        failures.append("OpenAI -> no OPENAI_API_KEY configured")

    # --- Fallback: OpenRouter free models ---
    if not OPENROUTER_API_KEY:
        failures.append("OpenRouter -> no OPENROUTER_API_KEY configured")
    else:
        for model in OPENROUTER_FALLBACKS:
            try:
                print(f"  trying OpenRouter/{model} ...", flush=True)
                return _try_model(openrouter_client, model, patient_info)
            except RateLimitError:
                failures.append(f"OpenRouter/{model} -> rate limited")
            except NotFoundError:
                failures.append(f"OpenRouter/{model} -> not found / unavailable")
            except (APIConnectionError, APITimeoutError):
                failures.append(f"OpenRouter/{model} -> connection or timeout error")
            except AuthenticationError:
                failures.append(f"OpenRouter/{model} -> authentication failed")
            except BadRequestError as e:
                failures.append(f"OpenRouter/{model} -> bad request ({e.status_code})")
            except APIError as e:
                failures.append(f"OpenRouter/{model} -> API error ({e.status_code})")
            except (json.JSONDecodeError, ValidationError):
                failures.append(f"OpenRouter/{model} -> invalid structured response")
            except Exception as e:
                failures.append(f"OpenRouter/{model} -> unexpected error ({type(e).__name__})")

    attempted = "\n  ".join(failures)
    raise RuntimeError(
        f"All {len(failures)} models failed:\n  {attempted}\n"
        "Check your API keys and try again."
    )


def build_patient_info(age: int, gender: str, severity: str, duration_days: int, symptoms: str) -> str:
    return (
        f"Age: {age}, Gender: {gender}, Severity: {severity}, "
        f"Duration: {duration_days} days, Symptoms: {symptoms}"
    )
