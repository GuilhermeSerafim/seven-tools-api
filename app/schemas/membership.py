import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator


class MembershipReviewUserSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    validation_status: str
    company_id: uuid.UUID | None = None


class MembershipReviewItemResponse(BaseModel):
    user: MembershipReviewUserSummaryResponse
    selected_company_name: str | None = None
    contact_email: str | None = None
    partner_1_name: str | None = None
    partner_2_name: str | None = None
    has_contract: bool = False
    requested_company_name: str | None = None
    requested_cnpj: str | None = None


class MembershipReviewListResponse(BaseModel):
    items: list[MembershipReviewItemResponse]


class MembershipApproveRequest(BaseModel):
    company_id: uuid.UUID | None = None
    create_company_from_request: bool = False

    @model_validator(mode="after")
    def validate_company_resolution(self):
        if self.company_id is not None and self.create_company_from_request:
            raise ValueError("Provide either company_id or create_company_from_request.")
        return self


class MembershipActionUserResponse(BaseModel):
    id: uuid.UUID
    validation_status: str
    approval_source: str | None = None
    approved_at: datetime | None = None
    approved_by_user_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None


class MembershipActionCompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    cnpj: str | None = None


class MembershipReviewActionResponse(BaseModel):
    user: MembershipActionUserResponse
    company: MembershipActionCompanyResponse | None = None


class MembershipClickupSyncResponse(BaseModel):
    synced: int
