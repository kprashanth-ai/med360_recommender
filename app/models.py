from typing import Literal
from pydantic import BaseModel, Field


class PatientInput(BaseModel):
    age: int = Field(..., ge=1, le=120, example=25)
    gender: Literal["male", "female", "other"]
    severity: Literal["low", "medium", "high"]
    duration_days: int = Field(..., ge=1, le=365, example=3)
    symptoms: str = Field(..., min_length=5, example="skin rash, itching, hives after eating")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class UsageSummary(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost_usd: float


class SpecialistPathwayItem(BaseModel):
    specialist: str
    reason: str


class RateLimitQuota(BaseModel):
    limit: int | None
    remaining: int | None
    reset: str | None


class RateLimitInfo(BaseModel):
    requests: RateLimitQuota
    tokens: RateLimitQuota


class UsageInfo(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_used: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    rate_limits: RateLimitInfo


class RecommendationResponse(BaseModel):
    recommended_specialist: str
    primary_recommendation_summary: str
    symptom_explanation: str
    specialist_pathway: list[SpecialistPathwayItem]
    red_flags: list[str]
    disclaimer: str
    usage: UsageInfo
