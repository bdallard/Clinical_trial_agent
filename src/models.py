"""Pydantic models for structured responses"""

from pydantic import BaseModel

class EligibilityCriteria(BaseModel):
    inclusion: list[str]
    exclusion: list[str]

class TrialSummary(BaseModel):
    nct_id: str
    title: str
    phase: str | None = None
    status: str | None = None
    sponsor: str | None = None
    enrollment: int | None = None
    start_date: str | None = None
    completion_date: str | None = None

class SiteSummary(BaseModel):
    nct_id: str
    facility: str
    city: str | None = None
    country: str | None = None

class FeasibilityResponse(BaseModel):
    answer: str
    trials: list[TrialSummary] | None = None
    sites: list[SiteSummary] | None = None
    criteria: EligibilityCriteria | None = None
    sources: list[str]


