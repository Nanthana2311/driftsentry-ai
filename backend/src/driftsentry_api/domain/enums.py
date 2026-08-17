from enum import StrEnum


class ModelTaskType(StrEnum):
    BINARY_CLASSIFICATION = "binary_classification"


class ModelStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class FeatureDataType(StrEnum):
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
