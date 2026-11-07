import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AnalysisType(str, enum.Enum):
    validation = "validation"
    diagnostic = "diagnostic"


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    type: Mapped[AnalysisType] = mapped_column(Enum(AnalysisType))
    input_data: Mapped[dict] = mapped_column(JSONB)
    output_data: Mapped[dict] = mapped_column(JSONB)
    score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="analysis_results")
