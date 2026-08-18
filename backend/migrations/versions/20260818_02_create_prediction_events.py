"""Create prediction event storage.

Revision ID: 20260818_02
Revises: 20260816_01
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_02"
down_revision: str | None = "20260816_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_models_ingestion_key_prefix",
        "models",
        ["ingestion_key_prefix"],
        unique=False,
    )
    op.create_table(
        "prediction_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("prediction", sa.Integer(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "prediction IN (0, 1)",
            name="binary_prediction",
        ),
        sa.CheckConstraint(
            "probability >= 0 AND probability <= 1",
            name="probability_range",
        ),
        sa.ForeignKeyConstraint(
            ["model_id"],
            ["models.id"],
            name="fk_prediction_events_model_id_models",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_prediction_events"),
        sa.UniqueConstraint(
            "model_id",
            "event_id",
            name="uq_prediction_events_model_event",
        ),
    )
    op.create_index(
        "ix_prediction_events_model_occurred",
        "prediction_events",
        ["model_id", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prediction_events_model_occurred",
        table_name="prediction_events",
    )
    op.drop_table("prediction_events")
    op.drop_index("ix_models_ingestion_key_prefix", table_name="models")
