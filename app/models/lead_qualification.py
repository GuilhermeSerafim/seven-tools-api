import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LeadTier(str, enum.Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    diamond = "diamond"


class LeadAction(str, enum.Enum):
    abordar_agora = "abordar_agora"
    revisar_manualmente = "revisar_manualmente"
    nutrir = "nutrir"
    descartar = "descartar"


class LeadStatus(str, enum.Enum):
    novo = "novo"
    em_andamento = "em_andamento"
    qualificado = "qualificado"
    nutrir = "nutrir"
    descartado = "descartado"


class LeadQualificationConfig(Base):
    __tablename__ = "lead_qualification_configs"
    __table_args__ = (UniqueConstraint("company_id", name="uq_lead_qualification_configs_company_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    ideal_segments: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    ideal_company_sizes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    ideal_roles: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    weight_segment: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_company_size: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_role: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_urgency: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_timing: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_pain_level: Mapped[int] = mapped_column(Integer, nullable=False)
    bronze_max: Mapped[int] = mapped_column(Integer, nullable=False)
    silver_max: Mapped[int] = mapped_column(Integer, nullable=False)
    gold_max: Mapped[int] = mapped_column(Integer, nullable=False)
    bronze_action: Mapped[LeadAction] = mapped_column(Enum(LeadAction), nullable=False)
    silver_action: Mapped[LeadAction] = mapped_column(Enum(LeadAction), nullable=False)
    gold_action: Mapped[LeadAction] = mapped_column(Enum(LeadAction), nullable=False)
    diamond_action: Mapped[LeadAction] = mapped_column(Enum(LeadAction), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    company: Mapped["Company"] = relationship()


class QualifiedLead(Base):
    __tablename__ = "qualified_leads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_role: Mapped[str] = mapped_column(String(255), nullable=False)
    segment: Mapped[str] = mapped_column(String(255), nullable=False)
    company_size: Mapped[str] = mapped_column(String(255), nullable=False)
    urgency: Mapped[str] = mapped_column(String(255), nullable=False)
    timing: Mapped[str] = mapped_column(String(255), nullable=False)
    pain_level: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), nullable=False, default=LeadStatus.novo)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tier: Mapped[LeadTier] = mapped_column(Enum(LeadTier), nullable=False, default=LeadTier.bronze)
    recommended_action: Mapped[LeadAction] = mapped_column(Enum(LeadAction), nullable=False, default=LeadAction.nutrir)
    scoring_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    company: Mapped["Company"] = relationship()
    created_by_user: Mapped["User"] = relationship()
