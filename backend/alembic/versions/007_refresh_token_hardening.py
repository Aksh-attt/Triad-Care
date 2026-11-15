"""007 – Refresh token hardening and data-driven demo profile isolation."""
from alembic import op
import sqlalchemy as sa

revision = "007_refresh_token_hardening"
down_revision = "006_hash_demo_passcodes"
branch_labels = None
depends_on = None

BACKUP_TABLE = "_m007_profile_is_demo_backup"


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Query active memberships only (status = 'active')
    # Inactive or suspended memberships must not cause false mixed-membership errors.
    rows = bind.execute(sa.text("""
        SELECT pm.profile_id, u.is_demo
        FROM profile_memberships pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.status = 'active'
    """)).fetchall()

    profile_members = {}
    for prof_id, is_demo in rows:
        profile_members.setdefault(prof_id, set()).add(bool(is_demo))

    demo_profiles = []
    for prof_id, flags in profile_members.items():
        if True in flags and False in flags:
            raise RuntimeError(
                f"Migration 007 aborted: Profile {prof_id} has inconsistent active membership "
                "(mixed demo and real users). Resolve membership before migration."
            )
        if flags == {True}:
            demo_profiles.append(prof_id)

    # 2. Record original is_demo values for profiles that this upgrade will modify
    inspector = sa.inspect(bind)
    if BACKUP_TABLE not in inspector.get_table_names():
        op.create_table(
            BACKUP_TABLE,
            sa.Column("profile_id", sa.Integer(), primary_key=True),
            sa.Column("orig_is_demo", sa.Integer(), nullable=False),
        )
    else:
        bind.execute(sa.text(f"DELETE FROM {BACKUP_TABLE}"))

    # Profiles with no active memberships remain unchanged (not in demo_profiles)
    if demo_profiles:
        # Check existing is_demo value of candidate demo profiles
        prof_rows = bind.execute(sa.text(
            f"SELECT id, is_demo FROM patient_profiles WHERE id IN ({','.join(str(p) for p in demo_profiles)})"
        )).fetchall()

        profiles_to_update = []
        for pid, curr_is_demo in prof_rows:
            # Only modify if current is_demo is not already 1 (True)
            if not bool(curr_is_demo):
                profiles_to_update.append(pid)
                bind.execute(
                    sa.text(
                        f"INSERT INTO {BACKUP_TABLE} (profile_id, orig_is_demo) VALUES (:pid, :orig)"
                    ),
                    {"pid": pid, "orig": int(curr_is_demo or 0)},
                )

        if profiles_to_update:
            bind.execute(
                sa.text(
                    f"UPDATE patient_profiles SET is_demo = 1 WHERE id IN ({','.join(str(p) for p in profiles_to_update)})"
                )
            )

    # 3. Add database-enforced uniqueness for non-null parent_token_id on refresh_tokens
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.create_unique_constraint(
            "uq_refresh_tokens_parent_token_id",
            ["parent_token_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # If the backup table does not exist, raise a clear RuntimeError before modifying any profile data.
    # Never guess or reset original is_demo values.
    if BACKUP_TABLE not in inspector.get_table_names():
        raise RuntimeError(
            f"Downgrade aborted: Tracking table '{BACKUP_TABLE}' not found. "
            "Cannot safely restore original profile is_demo values without backup data."
        )

    # 1. Drop unique constraint on refresh_tokens
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.drop_constraint("uq_refresh_tokens_parent_token_id", type_="unique")

    # 2. Reversible data migration: Restore original values from backup table
    backup_rows = bind.execute(sa.text(
        f"SELECT profile_id, orig_is_demo FROM {BACKUP_TABLE}"
    )).fetchall()
    for prof_id, orig_val in backup_rows:
        bind.execute(
            sa.text("UPDATE patient_profiles SET is_demo = :orig WHERE id = :pid"),
            {"orig": orig_val, "pid": prof_id},
        )

    # 3. Remove the temporary migration tracking data after successful downgrade
    op.drop_table(BACKUP_TABLE)
