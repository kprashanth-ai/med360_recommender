from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_DESCRIPTION, API_TITLE, API_VERSION, CORS_ALLOW_ORIGINS
from app.models import (
    HealthResponse,
    PatientInput,
    RateLimitInfo,
    RateLimitQuota,
    RecommendationResponse,
    UsageInfo,
    UsageSummary,
)
from app.services.llm import get_recommendation, build_patient_info
from app.tracker import get_session_totals

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "docs_url": "/docs",
        "health_url": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health():
    return HealthResponse(status="ok", service=API_TITLE, version=API_VERSION)


@app.get("/usage", response_model=UsageSummary, tags=["usage"])
def usage_summary():
    """Running totals across all logged requests (from logs/usage.json)."""
    return UsageSummary(**get_session_totals())


@app.post("/recommend", response_model=RecommendationResponse, tags=["recommendations"])
def recommend(patient: PatientInput):
    patient_info = build_patient_info(
        age=patient.age,
        gender=patient.gender,
        severity=patient.severity,
        duration_days=patient.duration_days,
        symptoms=patient.symptoms,
    )
    try:
        data, model_used, usage_entry = get_recommendation(patient_info)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return RecommendationResponse(
        recommended_specialist=data.get("recommended_specialist", "General Physician"),
        primary_recommendation_summary=data.get("primary_recommendation_summary", ""),
        symptom_explanation=data.get("symptom_explanation", ""),
        specialist_pathway=[
            {"specialist": item.get("specialist", ""), "reason": item.get("reason", "")}
            for item in data.get("specialist_pathway", [])
        ],
        red_flags=data.get("red_flags", []),
        disclaimer=data.get("disclaimer", ""),
        usage=UsageInfo(
            model_used=model_used,
            prompt_tokens=usage_entry["prompt_tokens"],
            completion_tokens=usage_entry["completion_tokens"],
            total_tokens=usage_entry["total_tokens"],
            cost_usd=usage_entry["cost_usd"],
            rate_limits=RateLimitInfo(
                requests=RateLimitQuota(**usage_entry["rate_limits"]["requests"]),
                tokens=RateLimitQuota(**usage_entry["rate_limits"]["tokens"]),
            ),
        ),
    )
