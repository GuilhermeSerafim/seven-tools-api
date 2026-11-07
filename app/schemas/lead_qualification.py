import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.lead_qualification import LeadAction, LeadStatus, LeadTier


class LeadQualificationConfigUpsert(BaseModel):
    ideal_segments: list[str]
    ideal_company_sizes: list[str]
    ideal_roles: list[str]
    weight_segment: int
    weight_company_size: int
    weight_role: int
    weight_urgency: int
    weight_timing: int
    weight_pain_level: int
    bronze_max: int
    silver_max: int
    gold_max: int
    bronze_action: LeadAction
    silver_action: LeadAction
    gold_action: LeadAction
    diamond_action: LeadAction


class LeadQualificationConfigResponse(LeadQualificationConfigUpsert):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QualifiedLeadCreate(BaseModel):
    contact_name: str
    company_name: str
    contact_role: str
    segment: str
    company_size: str
    urgency: str
    timing: str
    pain_level: str
    notes: str | None = None


class QualifiedLeadPatch(BaseModel):
    contact_name: str | None = None
    company_name: str | None = None
    contact_role: str | None = None
    segment: str | None = None
    company_size: str | None = None
    urgency: str | None = None
    timing: str | None = None
    pain_level: str | None = None
    notes: str | None = None
    status: LeadStatus | None = None


class QualifiedLeadResponse(QualifiedLeadCreate):
    id: uuid.UUID
    company_id: uuid.UUID
    created_by_user_id: uuid.UUID
    status: LeadStatus
    score: int
    tier: LeadTier
    recommended_action: LeadAction
    scoring_snapshot: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedQualifiedLeadResponse(BaseModel):
    items: list[QualifiedLeadResponse]
    total: int
    page: int
    per_page: int
