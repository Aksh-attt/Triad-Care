"""006 – Hash demo passcodes with Argon2id, set is_demo=True, drop plaintext passcode column."""
import sys
import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

# Ensure the backend package is importable when running from the backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


revision = "006_hash_demo_passcodes"
down_revision = "005_dose_confirmation_method"
branch_labels = None
depends_on = None

# Demo passcodes to hash (Meera=1111, Riya=2222, Arjun=3333)
DEMO_PASSCODES = {
    "1111": None,
    "2222": None,
    "3333": None,
}


def upgrade() -> None:
    from argon2 import PasswordHasher

    ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16)

    bind = op.get_bind()
    session = Session(bind=bind)

    # Fetch all users that still have a known demo passcode
    rows = session.execute(
        sa.text("SELECT id, passcode FROM users WHERE passcode IS NOT NULL")
    ).fetchall()

    for user_id, passcode in rows:
        if passcode in DEMO_PASSCODES:
            hashed = ph.hash(passcode)
            session.execute(
                sa.text(
                    "UPDATE users SET hashed_password = :h, is_demo = 1 WHERE id = :uid"
                ),
                {"h": hashed, "uid": user_id},
            )

    session.commit()

    # Verify: every demo user should now have a hashed_password
    missing = session.execute(
        sa.text(
            "SELECT id FROM users WHERE passcode IN ('1111','2222','3333') AND hashed_password IS NULL"
        )
    ).fetchall()
    if missing:
        raise RuntimeError(
            f"Migration 006 failed: {len(missing)} user(s) still have no hashed_password"
        )

    # Drop the plaintext passcode column using batch mode (required for SQLite)
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("passcode")


def downgrade() -> None:
    # Restore the passcode column (empty; we cannot recover plaintext from hashes)
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("passcode", sa.String(4), nullable=True))
