import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CompanyRequestStatus(str, enum.Enum):
    pending = "pending"
    resolved = "resolved"
    rejected = "rejected"


class CompanyRequest(Base):
    __tablename__ = "company_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    requested_company_name: Mapped[str] = mapped_column(String(255))
    requested_cnpj: Mapped[str | None] = mapped_column(String(18))
    status: Mapped[CompanyRequestStatus] = mapped_column(
        Enum(CompanyRequestStatus),
        default=CompanyRequestStatus.pending,
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="company_request")
