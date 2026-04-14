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

from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, FREE_MODEL_FALLBACKS
from app.models import LLMRecommendationPayload
from app.prompts import SYSTEM_PROMPT
from app.tracker import parse_rate_limits, record_usage

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)


def _normalize_recommendation_payload(raw_content: str) -> dict:
    payload = json.loads(raw_content)
    validated = LLMRecommendationPayload.model_validate(payload)
    return validated.model_dump()


def get_recommendation(patient_info: str) -> tuple[dict, str, dict]:
    """
    Try each model in FREE_MODEL_FALLBACKS until one succeeds.
    Returns (response_dict, model_used, usage_entry).
    Raises RuntimeError with per-model failure reasons if all fail.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured. Add it to your environment before calling /recommend."
        )

    failures: list[str] = []

    for model in FREE_MODEL_FALLBACKS:
        try:
            print(f"  trying {model} ...", flush=True)
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

        except RateLimitError:
            failures.append(f"{model} -> rate limited")
            continue
        except NotFoundError:
            failures.append(f"{model} -> not found / unavailable")
            continue
        except (APIConnectionError, APITimeoutError):
            failures.append(f"{model} -> connection or timeout error")
            continue
        except AuthenticationError:
            failures.append(f"{model} -> authentication failed")
            continue
        except BadRequestError as e:
            failures.append(f"{model} -> bad request ({e.status_code})")
            continue
        except APIError as e:
            failures.append(f"{model} -> API error ({e.status_code})")
            continue
        except (json.JSONDecodeError, ValidationError):
            failures.append(f"{model} -> invalid structured response")
            continue
        except Exception as e:
            failures.append(f"{model} -> unexpected error ({type(e).__name__})")
            continue

    attempted = "\n  ".join(failures)
    raise RuntimeError(
        f"All {len(failures)} models failed:\n  {attempted}\n"
        "Try again shortly or update FREE_MODEL_FALLBACKS in app/config.py."
    )


def build_patient_info(age: int, gender: str, severity: str, duration_days: int, symptoms: str) -> str:
    return (
        f"Age: {age}, Gender: {gender}, Severity: {severity}, "
        f"Duration: {duration_days} days, Symptoms: {symptoms}"
    )
