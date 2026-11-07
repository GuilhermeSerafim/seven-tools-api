import uuid

from pydantic import BaseModel


class RegistrationCompanyOption(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class RegistrationCompanyOptionsResponse(BaseModel):
    items: list[RegistrationCompanyOption]
