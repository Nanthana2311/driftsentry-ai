from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from driftsentry_api.domain.enums import FeatureDataType, ModelStatus, ModelTaskType

ModelName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=100,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
    ),
]
ModelVersion = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    ),
]
FeatureName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    ),
]


class FeatureCreate(BaseModel):
    name: FeatureName
    data_type: FeatureDataType
    nullable: bool = False
    constraints: dict[str, Any] = Field(default_factory=dict)


class ModelCreate(BaseModel):
    name: ModelName
    version: ModelVersion
    task_type: ModelTaskType = ModelTaskType.BINARY_CLASSIFICATION
    features: list[FeatureCreate] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def feature_names_must_be_unique(self) -> "ModelCreate":
        normalized = [feature.name.casefold() for feature in self.features]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Feature names must be unique within a model")
        return self


class FeatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    data_type: FeatureDataType
    nullable: bool
    constraints: dict[str, Any]
    position: int


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    version: str
    task_type: ModelTaskType
    status: ModelStatus
    ingestion_key_prefix: str
    monitoring_config: dict[str, Any]
    created_at: datetime
    features: list[FeatureResponse]


class ModelRegistrationResponse(ModelResponse):
    ingestion_key: str = Field(
        description="Returned once. Store it securely; DriftSentry stores only its hash."
    )


class ModelListResponse(BaseModel):
    items: list[ModelResponse]
    total: int
