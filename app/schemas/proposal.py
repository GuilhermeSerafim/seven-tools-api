# seven_tools_api/app/schemas/proposal.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class ProposalCreate(BaseModel):
    title: str
    client_name: str
    client_company: str | None = None
    client_email: str | None = None
    client_phone: str | None = None
    project_description: str | None = None
    scope: str | None = None
    value: str | None = None
    deadline: str | None = None
    notes: str | None = None
    status: str = "draft"


class ProposalPatch(BaseModel):
    title: str | None = None
    client_name: str | None = None
    client_company: str | None = None
    client_email: str | None = None
    client_phone: str | None = None
    project_description: str | None = None
    scope: str | None = None
    value: str | None = None
    deadline: str | None = None
    notes: str | None = None
    status: str | None = None


class ProposalResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    client_name: str
    client_company: str | None = None
    client_email: str | None = None
    client_phone: str | None = None
    project_description: str | None = None
    scope: str | None = None
    value: str | None = None
    deadline: str | None = None
    notes: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedProposalResponse(BaseModel):
    items: list[ProposalResponse]
    total: int
    page: int
    per_page: int
