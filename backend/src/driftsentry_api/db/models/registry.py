from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from driftsentry_api.db.base import Base
from driftsentry_api.db.types import JSON_DOCUMENT
from driftsentry_api.domain.enums import FeatureDataType, ModelStatus, ModelTaskType

if TYPE_CHECKING:
    from driftsentry_api.db.models.events import PredictionEvent


class RegisteredModel(Base):
    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_models_name_version"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    task_type: Mapped[ModelTaskType] = mapped_column(
        Enum(ModelTaskType, name="model_task_type", native_enum=False),
        nullable=False,
    )
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus, name="model_status", native_enum=False),
        default=ModelStatus.ACTIVE,
        nullable=False,
    )
    ingestion_key_prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ingestion_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    monitoring_config: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    features: Mapped[list["FeatureDefinition"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="FeatureDefinition.position",
    )
    prediction_events: Mapped[list["PredictionEvent"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class FeatureDefinition(Base):
    __tablename__ = "feature_definitions"
    __table_args__ = (UniqueConstraint("model_id", "name", name="uq_features_model_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    model_id: Mapped[UUID] = mapped_column(
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    data_type: Mapped[FeatureDataType] = mapped_column(
        Enum(FeatureDataType, name="feature_data_type", native_enum=False),
        nullable=False,
    )
    nullable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    constraints: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT,
        default=dict,
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    model: Mapped[RegisteredModel] = relationship(back_populates="features")
