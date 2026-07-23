from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ClassificationOut(BaseModel):
    incident_type: str
    relevance: str
    severity: int | None
    confidence: float
    abstained: bool
    model_name: str
    prompt_version: str


class ReviewOut(BaseModel):
    id: int
    classification_id: int
    reviewer: str
    decision: str
    notes: str | None
    reviewed_at: datetime


class IncidentSummary(BaseModel):
    id: int
    source: str
    url: str
    title: str
    published_at: datetime | None
    ingested_at: datetime
    classification: ClassificationOut | None


class IncidentDetail(IncidentSummary):
    body: str
    classifications: list[ClassificationOut]
    reviews: list[ReviewOut]


class ReviewIn(BaseModel):
    reviewer: str
    decision: str  # accept | override | false_positive
    notes: str | None = None


class Page(BaseModel):
    items: list[Any]
    total: int
    limit: int
    offset: int


class Stats(BaseModel):
    total_incidents: int
    total_classified: int
    abstention_rate: float
    by_incident_type: dict[str, int]
