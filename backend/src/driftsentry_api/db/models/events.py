from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy import UniqueConstraint as SQLUniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from driftsentry_api.db.base import Base
from driftsentry_api.db.types import JSON_DOCUMENT

if TYPE_CHECKING:
    from driftsentry_api.db.models.registry import RegisteredModel


class PredictionEvent(Base):
    __tablename__ = "prediction_events"
    __table_args__ = (
        SQLUniqueConstraint("model_id", "event_id", name="uq_prediction_events_model_event"),
        CheckConstraint(
            "probability >= 0 AND probability <= 1",
            name="probability_range",
        ),
        CheckConstraint("prediction IN (0, 1)", name="binary_prediction"),
        Index("ix_prediction_events_model_occurred", "model_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    model_id: Mapped[UUID] = mapped_column(
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    features: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    prediction: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    model: Mapped["RegisteredModel"] = relationship(back_populates="prediction_events")
