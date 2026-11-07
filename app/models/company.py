import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(255), default="manual")
    logo_url: Mapped[str | None] = mapped_column(String(500))
    website: Mapped[str | None] = mapped_column(String(500))
    instagram: Mapped[str | None] = mapped_column(String(255))
    segment: Mapped[str | None] = mapped_column(String(255))
    short_description: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(255))
    clickup_task_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    partner_1_name: Mapped[str | None] = mapped_column(String(255))
    partner_2_name: Mapped[str | None] = mapped_column(String(255))
    has_contract: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    clickup_status: Mapped[str | None] = mapped_column(String(255))
    clickup_tags: Mapped[list[str] | None] = mapped_column(MutableList.as_mutable(JSON))
    last_synced_at: Mapped[datetime | None]
    cnpj: Mapped[str | None] = mapped_column(String(18), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    users: Mapped[list["User"]] = relationship(back_populates="company")
