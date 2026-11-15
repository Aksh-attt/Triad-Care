"""008 – Add self-referencing foreign keys on refresh_tokens."""
from alembic import op
import sqlalchemy as sa

revision = "008_refresh_token_foreign_keys"
down_revision = "007_refresh_token_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.create_foreign_key(
            "fk_refresh_tokens_parent_token_id",
            "refresh_tokens",
            ["parent_token_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_refresh_tokens_replaced_by_token_id",
            "refresh_tokens",
            ["replaced_by_token_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.drop_constraint("fk_refresh_tokens_replaced_by_token_id", type_="foreignkey")
        batch_op.drop_constraint("fk_refresh_tokens_parent_token_id", type_="foreignkey")
