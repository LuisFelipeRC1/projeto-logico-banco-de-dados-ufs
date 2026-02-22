"""Implementa schema inicial do GeraLead.

Revision ID: 4c9f4d3baf45
Revises:
Create Date: 2025-10-03 09:44:28.992862
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c9f4d3baf45"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("cpf", sa.String(length=14), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "lead_searches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("params", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("results_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_lead_searches_user_id", "lead_searches", ["user_id"], unique=False)
    op.create_index("ix_lead_searches_user_started", "lead_searches", ["user_id", "started_at"], unique=False)

    op.create_table(
        "lead_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("search_id", sa.Integer(), nullable=False),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("opening_hours", sa.JSON(), nullable=True),
        sa.Column("place_name", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("reviews_count", sa.Integer(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["search_id"], ["lead_searches.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("search_id", "source_id", name="uq_search_source"),
    )
    op.create_index("ix_lead_results_search_id", "lead_results", ["search_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lead_results_search_id", table_name="lead_results")
    op.drop_table("lead_results")

    op.drop_index("ix_lead_searches_user_started", table_name="lead_searches")
    op.drop_index("ix_lead_searches_user_id", table_name="lead_searches")
    op.drop_table("lead_searches")

    op.drop_table("users")
