"""Add email notification delivery tracking

Revision ID: 73edab156ebe
Revises: 28bc1928a761
Create Date: 2026-08-28

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "73edab156ebe"
down_revision: Union[str, Sequence[str], None] = "28bc1928a761"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add email notification delivery tracking columns."""

    op.add_column(
        "lead_submission",
        sa.Column(
            "notification_status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
    )

    op.add_column(
        "lead_submission",
        sa.Column(
            "notification_sent_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "lead_submission",
        sa.Column(
            "notification_provider_id",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "lead_submission",
        sa.Column(
            "notification_error",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove email notification delivery tracking columns."""

    op.drop_column(
        "lead_submission",
        "notification_error",
    )

    op.drop_column(
        "lead_submission",
        "notification_provider_id",
    )

    op.drop_column(
        "lead_submission",
        "notification_sent_at",
    )

    op.drop_column(
        "lead_submission",
        "notification_status",
    )