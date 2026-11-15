"""004 – Add unique constraint (user_id, profile_id) on profile_memberships."""
from alembic import op


revision = "004_membership_uniqueness"
down_revision = "003_extend_memberships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("profile_memberships") as batch_op:
        batch_op.create_unique_constraint(
            "uq_membership_user_profile", ["user_id", "profile_id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("profile_memberships") as batch_op:
        batch_op.drop_constraint("uq_membership_user_profile", type_="unique")
