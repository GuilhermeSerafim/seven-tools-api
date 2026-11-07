# seven_tools_api/app/schemas/common.py
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    code: str
