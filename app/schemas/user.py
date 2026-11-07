# seven_tools_api/app/schemas/user.py
import uuid

from pydantic import BaseModel, EmailStr, field_validator


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    logo_url: str | None = None
    website: str | None = None
    instagram: str | None = None
    segment: str | None = None
    short_description: str | None = None
    city: str | None = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    validation_status: str
    approval_source: str | None = None
    must_change_password: bool = False
    job_title: str | None = None
    avatar_url: str | None = None
    instagram: str | None = None
    linkedin: str | None = None
    company: CompanyResponse | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    job_title: str | None = None
    avatar_url: str | None = None
    instagram: str | None = None
    linkedin: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str | None):
        if isinstance(value, str):
            return value.strip().lower()
        return value


class CompanyUpdate(BaseModel):
    name: str | None = None
    logo_url: str | None = None
    website: str | None = None
    instagram: str | None = None
    segment: str | None = None
    short_description: str | None = None
    city: str | None = None


class FavoriteResponse(BaseModel):
    tool_slugs: list[str]
