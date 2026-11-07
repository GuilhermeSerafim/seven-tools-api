import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(str, enum.Enum):
    admin = "admin"
    user = "user"


class ValidationStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    blocked = "blocked"


class ApprovalSource(str, enum.Enum):
    seed = "seed"
    manual = "manual"
    clickup_email_match = "clickup_email_match"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    __table_args__ = (
        Index("uq_users_email_lower", func.lower(email), unique=True),
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.user)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_status: Mapped[ValidationStatus] = mapped_column(
        Enum(ValidationStatus),
        default=ValidationStatus.pending_review,
    )
    approval_source: Mapped[ApprovalSource | None] = mapped_column(Enum(ApprovalSource))
    approved_at: Mapped[datetime | None]
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    job_title: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    instagram: Mapped[str | None] = mapped_column(String(255))
    linkedin: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    company: Mapped["Company | None"] = relationship(back_populates="users")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(back_populates="user")
    proposals: Mapped[list["Proposal"]] = relationship(back_populates="user")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(back_populates="user")
    company_request: Mapped["CompanyRequest | None"] = relationship(back_populates="user", uselist=False)
