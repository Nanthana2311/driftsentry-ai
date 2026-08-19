from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

EventId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$",
    ),
]
FeatureValue = bool | int | float | str | None


class PredictionEventCreate(BaseModel):
    event_id: EventId
    occurred_at: datetime
    features: dict[str, FeatureValue] = Field(min_length=1, max_length=200)
    prediction: Literal[0, 1]
    probability: float = Field(ge=0, le=1)

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class EventBatchCreate(BaseModel):
    events: list[PredictionEventCreate] = Field(min_length=1, max_length=500)

    @field_validator("events")
    @classmethod
    def event_ids_must_be_unique_in_batch(
        cls,
        events: list[PredictionEventCreate],
    ) -> list[PredictionEventCreate]:
        event_ids = [event.event_id for event in events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("event_id values must be unique within one batch")
        return events


class EventBatchResponse(BaseModel):
    model_id: UUID
    total: int
    accepted: int
    duplicates: int


class PredictionEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: str
    occurred_at: datetime
    features: dict[str, FeatureValue]
    prediction: int
    probability: float
    received_at: datetime


class EventListResponse(BaseModel):
    items: list[PredictionEventResponse]
    total: int
