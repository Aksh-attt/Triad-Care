"""005 – Add confirmation_method to dose_schedules."""
from alembic import op
import sqlalchemy as sa


revision = "005_dose_confirmation_method"
down_revision = "004_membership_uniqueness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("dose_schedules") as batch_op:
        batch_op.add_column(sa.Column("confirmation_method", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("dose_schedules") as batch_op:
        batch_op.drop_column("confirmation_method")
