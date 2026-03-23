"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "world_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("seed_id", sa.String(255), nullable=False),
        sa.Column("genesis_mode", sa.String(50), nullable=False),
        sa.Column("grid_width", sa.Integer(), nullable=False),
        sa.Column("grid_height", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("final_tick", sa.Integer(), nullable=True),
        sa.Column("final_population", sa.Integer(), nullable=True),
    )

    op.create_table(
        "agents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "world_run_id",
            sa.String(36),
            sa.ForeignKey("world_runs.id"),
            nullable=False,
        ),
        sa.Column("genome_hash", sa.String(16), nullable=False),
        sa.Column("genes_count", sa.Integer(), nullable=False),
        sa.Column("birth_tick", sa.Integer(), nullable=False),
        sa.Column("death_tick", sa.Integer(), nullable=True),
        sa.Column("parent_ids", postgresql.JSONB(), server_default="[]"),
        sa.Column("species_label", sa.String(100), nullable=True),
        sa.Column("final_energy", sa.Float(), nullable=True),
        sa.Column("final_health", sa.Float(), nullable=True),
        sa.Column("final_mass", sa.Float(), nullable=True),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "world_run_id",
            sa.String(36),
            sa.ForeignKey("world_runs.id"),
            nullable=False,
        ),
        sa.Column("tick", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("target_id", sa.String(36), nullable=True),
        sa.Column("data", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_events_tick", "events", ["tick"])
    op.create_index("ix_events_type", "events", ["event_type"])
    op.create_index("ix_events_world_tick", "events", ["world_run_id", "tick"])

    op.create_table(
        "species",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "world_run_id",
            sa.String(36),
            sa.ForeignKey("world_runs.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("first_seen_tick", sa.Integer(), nullable=False),
        sa.Column("peak_population", sa.Integer(), server_default="0"),
        sa.Column("total_born", sa.Integer(), server_default="0"),
        sa.Column("total_died", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "metrics_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "world_run_id",
            sa.String(36),
            sa.ForeignKey("world_runs.id"),
            nullable=False,
        ),
        sa.Column("tick", sa.Integer(), nullable=False),
        sa.Column("population", sa.Integer(), nullable=False),
        sa.Column("total_energy", sa.Float(), nullable=False),
        sa.Column("shannon_entropy", sa.Float(), nullable=True),
        sa.Column("genome_diversity", sa.Float(), nullable=True),
        sa.Column("avg_neural_complexity", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_metrics_tick", "metrics_snapshots", ["tick"])


def downgrade() -> None:
    op.drop_table("metrics_snapshots")
    op.drop_table("species")
    op.drop_table("events")
    op.drop_table("agents")
    op.drop_table("world_runs")
