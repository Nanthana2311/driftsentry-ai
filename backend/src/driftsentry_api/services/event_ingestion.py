from collections.abc import Mapping
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import Select, Table, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from driftsentry_api.db.models import FeatureDefinition, PredictionEvent, RegisteredModel
from driftsentry_api.domain.enums import FeatureDataType
from driftsentry_api.schemas.events import EventBatchCreate, PredictionEventCreate


class FeatureSchemaValidationError(Exception):
    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__("Prediction features do not match the registered model schema")
        self.errors = errors


class EventIngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ingest(
        self,
        model: RegisteredModel,
        payload: EventBatchCreate,
    ) -> tuple[int, int]:
        errors: list[dict[str, Any]] = []
        feature_map = {feature.name: feature for feature in model.features}
        for event in payload.events:
            errors.extend(_validate_event(event, feature_map))
        if errors:
            raise FeatureSchemaValidationError(errors)

        values = [
            {
                "id": uuid4(),
                "model_id": model.id,
                "event_id": event.event_id,
                "occurred_at": event.occurred_at,
                "features": event.features,
                "prediction": event.prediction,
                "probability": event.probability,
            }
            for event in payload.events
        ]
        table = cast(Table, PredictionEvent.__table__)
        dialect_name = self.session.get_bind().dialect.name
        statement: Any
        if dialect_name == "postgresql":
            statement = postgres_insert(table).values(values)
        elif dialect_name == "sqlite":
            statement = sqlite_insert(table).values(values)
        else:  # pragma: no cover - MVP supports PostgreSQL and test SQLite.
            raise RuntimeError(f"Unsupported database dialect: {dialect_name}")

        statement = statement.on_conflict_do_nothing(
            index_elements=[table.c.model_id, table.c.event_id]
        ).returning(table.c.event_id)
        inserted_ids = list((await self.session.execute(statement)).scalars().all())
        await self.session.commit()

        accepted = len(inserted_ids)
        return accepted, len(payload.events) - accepted

    async def list_for_model(
        self,
        model_id: UUID,
        limit: int,
    ) -> list[PredictionEvent]:
        statement: Select[tuple[PredictionEvent]] = (
            select(PredictionEvent)
            .where(PredictionEvent.model_id == model_id)
            .order_by(PredictionEvent.occurred_at.desc())
            .limit(limit)
        )
        return list((await self.session.scalars(statement)).all())


def _validate_event(
    event: PredictionEventCreate,
    feature_map: Mapping[str, FeatureDefinition],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = set(feature_map)
    received = set(event.features)

    for name in sorted(expected - received):
        errors.append(_error(event.event_id, name, "missing_feature", "Feature is required"))
    for name in sorted(received - expected):
        errors.append(_error(event.event_id, name, "unknown_feature", "Feature is not registered"))

    for name in sorted(expected & received):
        feature = feature_map[name]
        value = event.features[name]
        if value is None:
            if not feature.nullable:
                errors.append(
                    _error(event.event_id, name, "null_not_allowed", "Null is not allowed")
                )
            continue

        if feature.data_type is FeatureDataType.NUMERICAL:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(_error(event.event_id, name, "invalid_type", "Expected a number"))
                continue
            minimum = feature.constraints.get("min")
            maximum = feature.constraints.get("max")
            if isinstance(minimum, (int, float)) and value < minimum:
                errors.append(
                    _error(event.event_id, name, "below_minimum", f"Minimum is {minimum}")
                )
            if isinstance(maximum, (int, float)) and value > maximum:
                errors.append(
                    _error(event.event_id, name, "above_maximum", f"Maximum is {maximum}")
                )
        elif feature.data_type is FeatureDataType.CATEGORICAL:
            if not isinstance(value, str):
                errors.append(_error(event.event_id, name, "invalid_type", "Expected a string"))
                continue
            allowed = feature.constraints.get("allowed")
            if isinstance(allowed, list) and value not in allowed:
                errors.append(
                    _error(event.event_id, name, "value_not_allowed", "Category is not allowed")
                )
        elif feature.data_type is FeatureDataType.BOOLEAN and not isinstance(value, bool):
            errors.append(_error(event.event_id, name, "invalid_type", "Expected a boolean"))

    return errors


def _error(event_id: str, feature: str, code: str, message: str) -> dict[str, str]:
    return {
        "event_id": event_id,
        "feature": feature,
        "code": code,
        "message": message,
    }
