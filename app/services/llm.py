import json
from openai import OpenAI, RateLimitError, NotFoundError, APIError

from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, FREE_MODEL_FALLBACKS
from app.prompts import SYSTEM_PROMPT
from app.tracker import parse_rate_limits, record_usage

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)


def get_recommendation(patient_info: str) -> tuple[dict, str, dict]:
    """
    Try each model in FREE_MODEL_FALLBACKS until one succeeds.
    Returns (response_dict, model_used, usage_entry).
    Raises RuntimeError with per-model failure reasons if all fail.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not configured. Add it to your environment before calling /recommend.")

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

            data = json.loads(response.choices[0].message.content)
            return data, model, usage_entry

        except RateLimitError:
            failures.append(f"{model} → rate limited")
            continue
        except NotFoundError:
            failures.append(f"{model} → not found / unavailable")
            continue
        except APIError as e:
            failures.append(f"{model} → API error ({e.status_code})")
            continue
        except json.JSONDecodeError:
            failures.append(f"{model} → bad JSON in response")
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
