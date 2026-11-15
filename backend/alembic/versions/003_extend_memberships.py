"""003 – Extend profile_memberships with status, relationship_label, permissions, updated_at."""
from alembic import op
import sqlalchemy as sa


revision = "003_extend_memberships"
down_revision = "002_create_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("profile_memberships") as batch_op:
        batch_op.add_column(sa.Column("relationship_label", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("status", sa.String(), nullable=False, server_default="active")
        )
        batch_op.add_column(
            sa.Column("permissions", sa.JSON(), nullable=False, server_default="{}")
        )
        batch_op.add_column(
            sa.Column("updated_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now())
        )


def downgrade() -> None:
    with op.batch_alter_table("profile_memberships") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("permissions")
        batch_op.drop_column("status")
        batch_op.drop_column("relationship_label")
