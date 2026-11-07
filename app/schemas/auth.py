# seven_tools_api/app/schemas/auth.py
import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str):
        if isinstance(value, str):
            return value.strip().lower()
        return value


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    company_id: uuid.UUID | None = None
    other_company_name: str | None = None
    other_company_cnpj: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("other_company_name", "other_company_cnpj", mode="before")
    @classmethod
    def strip_optional_text(cls, value: str | None):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_company_selection(self):
        has_company_id = self.company_id is not None
        has_other_name = self.other_company_name is not None
        has_other_cnpj = self.other_company_cnpj is not None

        if has_company_id and (has_other_name or has_other_cnpj):
            raise ValueError("Provide either company_id or other_company_name with other_company_cnpj.")

        if not has_company_id and not has_other_name and not has_other_cnpj:
            raise ValueError("Provide company_id or other_company_name with other_company_cnpj.")

        if not has_company_id and has_other_name != has_other_cnpj:
            raise ValueError("Provide both other_company_name and other_company_cnpj.")

        return self


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

    @model_validator(mode="after")
    def passwords_must_differ(self):
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current password.")
        return self


class PasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str):
        if isinstance(value, str):
            return value.strip().lower()
        return value


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., min_length=20)
    new_password: str = Field(..., min_length=6)


class AuthResponse(BaseModel):
    token: str
    user: "AuthUserResponse"


class AuthUserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    validation_status: str
    approval_source: str | None = None
    company_id: uuid.UUID | None = None
    must_change_password: bool = False

    model_config = {"from_attributes": True}
