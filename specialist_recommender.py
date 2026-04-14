from app.services.llm import build_patient_info, get_recommendation
from app.tracker import get_session_totals


def main():
    print("Specialist Recommender")
    print("=" * 40)
    age = int(input("Age: ").strip())
    gender = input("Gender (male/female/other): ").strip().lower()
    severity = input("Severity (low/medium/high): ").strip().lower()
    duration = int(input("Duration (in days): ").strip())
    symptoms = input("Describe your symptoms: ").strip()

    if not symptoms:
        print("No symptoms provided.")
        return

    patient_info = build_patient_info(age, gender, severity, duration, symptoms)

    print("\nAnalyzing...")
    try:
        data, model_used, usage_entry = get_recommendation(patient_info)
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    print("\nRecommendation")
    print(f"Specialist         : {data.get('recommended_specialist')}")
    print(f"Summary            : {data.get('primary_recommendation_summary')}")
    print(f"What this may mean : {data.get('symptom_explanation')}")
    print("Possible Next Specialists:")
    for item in data.get("specialist_pathway", []):
        print(f"  - {item.get('specialist')}: {item.get('reason')}")
    print("Red Flags:")
    for item in data.get("red_flags", []):
        print(f"  - {item}")
    print(f"Disclaimer         : {data.get('disclaimer')}")

    print("\n--- Usage ---")
    rl = usage_entry.get("rate_limits", {})
    req = rl.get("requests", {})
    tok = rl.get("tokens", {})

    print(f"Model              : {model_used}")
    print(
        f"Tokens this call   : {usage_entry.get('total_tokens')} "
        f"(prompt: {usage_entry.get('prompt_tokens')}, "
        f"completion: {usage_entry.get('completion_tokens')})"
    )
    print(f"Cost this call     : ${usage_entry.get('cost_usd', 0):.6f}")

    if req.get("remaining") is not None:
        reset_str = f"  - resets {req['reset']}" if req.get("reset") else ""
        print(f"Requests today     : {req['remaining']} / {req['limit']} remaining{reset_str}")
    else:
        print("Requests today     : not reported by provider for this model")

    if tok.get("remaining") is not None:
        reset_str = f"  - resets {tok['reset']}" if tok.get("reset") else ""
        print(f"Tokens today       : {tok['remaining']} / {tok['limit']} remaining{reset_str}")
    else:
        print("Tokens today       : not reported by provider for this model")

    totals = get_session_totals()
    print(
        f"\nSession totals     : {totals['total_requests']} requests | "
        f"{totals['total_tokens']} tokens | ${totals['total_cost_usd']:.6f}"
    )


if __name__ == "__main__":
    main()
