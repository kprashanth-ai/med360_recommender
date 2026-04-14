import streamlit as st
from app.services.llm import get_recommendation, build_patient_info
from app.tracker import get_session_totals

st.set_page_config(page_title="Specialist Recommender", page_icon="🏥")
st.title("🏥 Specialist Recommender")
st.caption("AI-assisted triage for consultation booking only.")

with st.form("patient_form"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=1, max_value=120, value=30)
        gender = st.selectbox("Gender", ["male", "female", "other"])
    with col2:
        severity = st.selectbox("Severity", ["low", "medium", "high"])
        duration = st.number_input("Duration (days)", min_value=1, max_value=365, value=3)

    symptoms = st.text_area(
        "Describe your symptoms",
        placeholder="e.g. skin rash, itching, hives after eating...",
    )
    submitted = st.form_submit_button("Get Recommendation", type="primary")

if submitted:
    if not symptoms.strip():
        st.warning("Please describe your symptoms.")
    else:
        patient_info = build_patient_info(age, gender, severity, int(duration), symptoms)
        with st.spinner("Analyzing..."):
            try:
                data, model_used, usage_entry = get_recommendation(patient_info)
            except RuntimeError as e:
                st.error(str(e))
                st.stop()

        st.success(f"**Recommended Specialist:** {data.get('recommended_specialist')}")
        st.info(f"**Summary:** {data.get('primary_recommendation_summary')}")
        st.markdown(f"**What this may mean:** {data.get('symptom_explanation')}")

        st.subheader("Possible Next Specialists")
        for item in data.get("specialist_pathway", []):
            st.markdown(f"- **{item.get('specialist')}**: {item.get('reason')}")

        st.subheader("Red Flags — Seek Immediate Care If:")
        for flag in data.get("red_flags", []):
            st.markdown(f"- {flag}")

        st.warning(data.get("disclaimer"))

        # --- Usage panel ---
        with st.expander("Usage & Cost", expanded=True):
            rl  = usage_entry.get("rate_limits", {})
            req = rl.get("requests", {})
            tok = rl.get("tokens", {})

            col1, col2, col3 = st.columns(3)
            col1.metric("Model", model_used.split("/")[-1])
            col2.metric("Tokens this call", usage_entry.get("total_tokens", 0))
            col3.metric("Cost this call", f"${usage_entry.get('cost_usd', 0):.6f}")

            if req.get("remaining") is not None:
                pct = int(req["remaining"] / req["limit"] * 100) if req.get("limit") else 0
                st.progress(pct / 100, text=f"Requests today: **{req['remaining']} / {req['limit']}** remaining"
                            + (f"  |  Resets: {req['reset']}" if req.get("reset") else ""))
            if tok.get("remaining") is not None:
                pct = int(tok["remaining"] / tok["limit"] * 100) if tok.get("limit") else 0
                st.progress(pct / 100, text=f"Tokens today: **{tok['remaining']} / {tok['limit']}** remaining"
                            + (f"  |  Resets: {tok['reset']}" if tok.get("reset") else ""))

        totals = get_session_totals()
        st.caption(
            f"Session totals — {totals['total_requests']} requests | "
            f"{totals['total_tokens']} tokens | "
            f"${totals['total_cost_usd']:.6f}"
        )
