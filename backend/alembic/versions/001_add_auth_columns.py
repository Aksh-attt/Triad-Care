"""001 – Add hashed_password, is_active, is_demo to users; add is_demo to patient_profiles."""
from alembic import op
import sqlalchemy as sa


revision = "001_add_auth_columns"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("hashed_password", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("is_demo", sa.Boolean(), nullable=False, server_default="0"))

    with op.batch_alter_table("patient_profiles") as batch_op:
        batch_op.add_column(sa.Column("is_demo", sa.Boolean(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("patient_profiles") as batch_op:
        batch_op.drop_column("is_demo")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_demo")
        batch_op.drop_column("is_active")
        batch_op.drop_column("hashed_password")
