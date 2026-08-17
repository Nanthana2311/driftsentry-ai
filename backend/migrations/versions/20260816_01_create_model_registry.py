"""Create model registry tables.

Revision ID: 20260816_01
Revises: None
Create Date: 2026-08-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260816_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

model_task_type = sa.Enum(
    "BINARY_CLASSIFICATION",
    name="model_task_type",
    native_enum=False,
)
model_status = sa.Enum("ACTIVE", "PAUSED", "ARCHIVED", name="model_status", native_enum=False)
feature_data_type = sa.Enum(
    "NUMERICAL",
    "CATEGORICAL",
    "BOOLEAN",
    name="feature_data_type",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "models",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("task_type", model_task_type, nullable=False),
        sa.Column("status", model_status, nullable=False),
        sa.Column("ingestion_key_prefix", sa.String(length=20), nullable=False),
        sa.Column("ingestion_key_hash", sa.String(length=64), nullable=False),
        sa.Column("monitoring_config", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_models"),
        sa.UniqueConstraint("name", "version", name="uq_models_name_version"),
    )
    op.create_table(
        "feature_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("data_type", feature_data_type, nullable=False),
        sa.Column("nullable", sa.Boolean(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["model_id"],
            ["models.id"],
            name="fk_feature_definitions_model_id_models",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_feature_definitions"),
        sa.UniqueConstraint("model_id", "name", name="uq_features_model_name"),
    )
    op.create_index(
        "ix_feature_definitions_model_id",
        "feature_definitions",
        ["model_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_feature_definitions_model_id", table_name="feature_definitions")
    op.drop_table("feature_definitions")
    op.drop_table("models")
