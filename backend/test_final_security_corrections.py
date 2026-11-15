"""
test_final_security_corrections.py – Verification of Final Security Review Corrections

Covers:
  1. Normal upgrade and downgrade restore original values correctly using fresh Alembic migration chain.
  2. Pre-existing demo profiles remain demo across upgrade and downgrade.
  3. Missing backup table causes downgrade to fail safely without changing profile flags.
  4. Mixed active memberships abort without partial changes.
  5. Inactive and suspended memberships are ignored during classification.
  6. Migration 008 still applies successfully after migration 007 on a fresh database.
  7. Missing FRONTEND_URL in production mode prevents startup.
  8. Insecure HTTP origins rejected in production CORS configuration.
  9. Production localhost and loopback origins rejected in production CORS configuration.
  10. Valid production origins accepted.
  11. Development CORS defaults to localhost support.
  12. Production FastAPI lifespan aborts startup on invalid CORS configuration.
  13. JWT secret is never leaked in exception messages or logs.
  14. Refresh-token rotation and replay revocation continue to operate correctly.
"""

import os
import sqlite3
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient
from alembic.config import Config
from alembic import command

from main import app, validate_cors_configuration
from auth_utils import validate_jwt_configuration, DEFAULT_INSECURE_SECRET
from database import engine as app_engine

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ALEMBIC_INI = os.path.join(BACKEND_DIR, "alembic.ini")


@pytest.fixture
def fresh_alembic_006_db(tmp_path):
    """
    Create a genuinely empty temporary SQLite database and run the real
    Alembic migration chain from base through 006_hash_demo_passcodes.
    Does NOT copy any existing caresync.db.
    """
    db_file = str(tmp_path / "fresh_migration_test.db")

    # Initial pre-migration baseline schema (state prior to migration 001)
    conn = sqlite3.connect(db_file)
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            email VARCHAR UNIQUE,
            role VARCHAR NOT NULL,
            passcode VARCHAR(4)
        );
        CREATE TABLE patient_profiles (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL
        );
        CREATE TABLE profile_memberships (
            id INTEGER PRIMARY KEY,
            profile_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role VARCHAR NOT NULL
        );
        CREATE TABLE dose_schedules (
            id INTEGER PRIMARY KEY,
            status VARCHAR DEFAULT 'scheduled'
        );
    """)
    conn.commit()
    conn.close()

    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_file}")

    # Run real Alembic migration chain from base through 006_hash_demo_passcodes
    command.upgrade(cfg, "006_hash_demo_passcodes")

    yield db_file, cfg


# ===========================================================================
# 1. Normal Upgrade and Downgrade Restore Original Values Correctly
# ===========================================================================
def test_migration_007_normal_upgrade_downgrade_restores_original_values(fresh_alembic_006_db):
    """Verify normal upgrade sets demo flag and downgrade restores original value."""
    db_file, cfg = fresh_alembic_006_db

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("INSERT INTO users (id, name, email, role, is_demo, is_active) VALUES (1, 'Demo User', 'd1@test.com', 'caregiver', 1, 1)")
    c.execute("INSERT INTO users (id, name, email, role, is_demo, is_active) VALUES (2, 'Real User', 'r2@test.com', 'caregiver', 0, 1)")

    # Profile 1: is_demo = 0 initially, exclusively active demo member
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (1, 'Demo Target Profile', 0)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (1, 1, 1, 'caregiver', 'active')")

    # Profile 2: is_demo = 0 initially, exclusively active real member
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (2, 'Real Target Profile', 0)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (2, 2, 2, 'caregiver', 'active')")
    conn.commit()
    conn.close()

    # Upgrade to 007
    command.upgrade(cfg, "007_refresh_token_hardening")

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    p1_up = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 1").fetchone()[0]
    p2_up = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 2").fetchone()[0]
    assert p1_up == 1, "Profile 1 was not updated to is_demo = 1"
    assert p2_up == 0, "Profile 2 was incorrectly modified"

    # Verify backup table recorded profile 1
    backup_rows = c.execute("SELECT profile_id, orig_is_demo FROM _m007_profile_is_demo_backup").fetchall()
    assert (1, 0) in backup_rows
    conn.close()

    # Downgrade to 006
    command.downgrade(cfg, "006_hash_demo_passcodes")

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    p1_down = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 1").fetchone()[0]
    p2_down = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 2").fetchone()[0]
    assert p1_down == 0, "Profile 1 was not restored to original value (0)"
    assert p2_down == 0, "Profile 2 was changed"

    # Backup table must be dropped
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "_m007_profile_is_demo_backup" not in tables, "Backup table was not dropped"
    conn.close()


# ===========================================================================
# 2. Pre-Existing Demo Profiles Remain Demo
# ===========================================================================
def test_migration_007_pre_existing_demo_profiles_remain_demo(fresh_alembic_006_db):
    """Verify pre-existing demo profiles (is_demo=1 before migration) remain 1 on downgrade."""
    db_file, cfg = fresh_alembic_006_db

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("INSERT INTO users (id, name, email, role, is_demo, is_active) VALUES (1, 'Demo User', 'd1@test.com', 'caregiver', 1, 1)")

    # Pre-existing demo profile already has is_demo = 1
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (10, 'Pre-existing Demo Profile', 1)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (10, 10, 1, 'caregiver', 'active')")
    conn.commit()
    conn.close()

    # Upgrade to 007
    command.upgrade(cfg, "007_refresh_token_hardening")

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    p10_up = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 10").fetchone()[0]
    assert p10_up == 1

    # Verify it was NOT recorded in backup table because it was not modified
    backup_rows = c.execute("SELECT profile_id FROM _m007_profile_is_demo_backup").fetchall()
    assert 10 not in [r[0] for r in backup_rows]
    conn.close()

    # Downgrade to 006
    command.downgrade(cfg, "006_hash_demo_passcodes")

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    p10_down = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 10").fetchone()[0]
    assert p10_down == 1, "Pre-existing demo profile was incorrectly reset to 0 during downgrade!"
    conn.close()


# ===========================================================================
# 3. Missing Backup Table Causes Downgrade to Fail Safely Without Modifying Flags
# ===========================================================================
def test_migration_007_missing_backup_table_fails_safely(fresh_alembic_006_db):
    """Missing backup table must raise RuntimeError on downgrade before changing profile flags."""
    db_file, cfg = fresh_alembic_006_db

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("INSERT INTO users (id, name, email, role, is_demo, is_active) VALUES (1, 'Demo User', 'd1@test.com', 'caregiver', 1, 1)")
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (20, 'Demo Profile', 0)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (20, 20, 1, 'caregiver', 'active')")
    conn.commit()
    conn.close()

    # Upgrade to 007
    command.upgrade(cfg, "007_refresh_token_hardening")

    # Intentionally drop the backup table to simulate missing backup state
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("DROP TABLE _m007_profile_is_demo_backup")
    conn.commit()
    conn.close()

    # Downgrade MUST raise RuntimeError
    with pytest.raises(Exception) as exc_info:
        command.downgrade(cfg, "006_hash_demo_passcodes")

    assert "not found" in str(exc_info.value).lower()

    # Verify profile 20 flag was NOT guessed or modified (fails safely)
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    p20_after = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 20").fetchone()[0]
    assert p20_after == 1, "Profile flag was improperly modified when backup table was missing"
    conn.close()


# ===========================================================================
# 4. Mixed Active Memberships Abort Without Partial Changes
# ===========================================================================
def test_migration_007_mixed_active_memberships_abort_safely(fresh_alembic_006_db):
    """Mixed active memberships must abort migration safely without partial changes."""
    db_file, cfg = fresh_alembic_006_db

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("INSERT INTO users (id, name, email, role, is_demo, is_active) VALUES (1, 'Demo User', 'd1@test.com', 'caregiver', 1, 1)")
    c.execute("INSERT INTO users (id, name, email, role, is_demo, is_active) VALUES (2, 'Real User', 'r2@test.com', 'caregiver', 0, 1)")

    # Profile 30 has BOTH active demo and active real members
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (30, 'Mixed Active Profile', 0)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (30, 30, 1, 'caregiver', 'active')")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (31, 30, 2, 'caregiver', 'active')")

    # Profile 31 is pure demo
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (31, 'Pure Demo Profile', 0)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (32, 31, 1, 'caregiver', 'active')")
    conn.commit()
    conn.close()

    # Upgrade MUST fail
    with pytest.raises(Exception) as exc_info:
        command.upgrade(cfg, "007_refresh_token_hardening")

    assert "inconsistent active membership" in str(exc_info.value).lower()

    # Verify no partial changes occurred
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    p30 = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 30").fetchone()[0]
    p31 = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 31").fetchone()[0]
    assert p30 == 0, "Profile 30 was partially modified"
    assert p31 == 0, "Profile 31 was partially modified"

    # Unique constraint was NOT applied
    indices = [r[1] for r in c.execute("PRAGMA index_list(refresh_tokens)").fetchall()]
    assert "uq_refresh_tokens_parent_token_id" not in indices
    conn.close()


# ===========================================================================
# 5. Inactive and Suspended Memberships Are Ignored
# ===========================================================================
def test_migration_007_inactive_and_suspended_memberships_ignored(fresh_alembic_006_db):
    """Inactive and suspended memberships must not cause false mixed-membership aborts."""
    db_file, cfg = fresh_alembic_006_db

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("INSERT INTO users (id, name, email, role, is_demo, is_active) VALUES (1, 'Demo User', 'd1@test.com', 'caregiver', 1, 1)")
    c.execute("INSERT INTO users (id, name, email, role, is_demo, is_active) VALUES (2, 'Real User', 'r2@test.com', 'caregiver', 0, 1)")

    # Profile 40: Active demo + Inactive real
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (40, 'Active demo, inactive real', 0)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (40, 40, 1, 'caregiver', 'active')")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (41, 40, 2, 'caregiver', 'inactive')")

    # Profile 41: Active demo + Suspended real
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (41, 'Active demo, suspended real', 0)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (42, 41, 1, 'caregiver', 'active')")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (43, 41, 2, 'caregiver', 'suspended')")

    # Profile 42: Active real + Inactive demo
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (42, 'Active real, inactive demo', 0)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (44, 42, 2, 'caregiver', 'active')")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (45, 42, 1, 'caregiver', 'inactive')")

    # Profile 43: No active memberships (inactive only)
    c.execute("INSERT INTO patient_profiles (id, name, is_demo) VALUES (43, 'No active memberships', 0)")
    c.execute("INSERT INTO profile_memberships (id, profile_id, user_id, role, status) VALUES (46, 43, 1, 'caregiver', 'inactive')")
    conn.commit()
    conn.close()

    # Must upgrade cleanly without error
    command.upgrade(cfg, "007_refresh_token_hardening")

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    p40 = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 40").fetchone()[0]
    p41 = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 41").fetchone()[0]
    p42 = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 42").fetchone()[0]
    p43 = c.execute("SELECT is_demo FROM patient_profiles WHERE id = 43").fetchone()[0]

    assert p40 == 1, "Profile 40 with active demo should become demo"
    assert p41 == 1, "Profile 41 with active demo should become demo"
    assert p42 == 0, "Profile 42 with active real should remain real"
    assert p43 == 0, "Profile 43 with no active memberships should remain unchanged"
    conn.close()


# ===========================================================================
# 6. Migration 008 Applies Successfully After Migration 007 On Fresh DB
# ===========================================================================
def test_migration_008_applies_successfully_after_007(fresh_alembic_006_db):
    """Verify migration 008 applies on top of 007 in fresh database and creates foreign keys."""
    db_file, cfg = fresh_alembic_006_db

    # Upgrade to 007
    command.upgrade(cfg, "007_refresh_token_hardening")

    # Upgrade to 008
    command.upgrade(cfg, "008_refresh_token_foreign_keys")

    conn = sqlite3.connect(db_file)
    fk_list = conn.execute("PRAGMA foreign_key_list(refresh_tokens)").fetchall()
    conn.close()

    fk_map = {row[3]: (row[2], row[4], row[6]) for row in fk_list}
    assert "parent_token_id" in fk_map, "parent_token_id foreign key missing"
    assert fk_map["parent_token_id"] == ("refresh_tokens", "id", "SET NULL")
    assert "replaced_by_token_id" in fk_map, "replaced_by_token_id foreign key missing"
    assert fk_map["replaced_by_token_id"] == ("refresh_tokens", "id", "SET NULL")


# ===========================================================================
# 7. Missing FRONTEND_URL In Production Mode Prevents Startup
# ===========================================================================
def test_production_cors_missing_frontend_url_raises():
    """In production, missing FRONTEND_URL must raise RuntimeError."""
    with pytest.raises(RuntimeError) as exc_info:
        validate_cors_configuration(env="production", frontend_url=None)
    assert "FRONTEND_URL must be explicitly set" in str(exc_info.value)

    with pytest.raises(RuntimeError) as exc_info:
        validate_cors_configuration(env="production", frontend_url="")
    assert "FRONTEND_URL must be explicitly set" in str(exc_info.value)


# ===========================================================================
# 8. Insecure HTTP Scheme Rejected In Production CORS
# ===========================================================================
def test_production_cors_insecure_http_scheme_rejected():
    """In production, HTTP schemes must be rejected."""
    with pytest.raises(RuntimeError) as exc_info:
        validate_cors_configuration(env="production", frontend_url="http://triadcare.example.com")
    assert "must use HTTPS scheme" in str(exc_info.value)

    with pytest.raises(RuntimeError) as exc_info:
        validate_cors_configuration(
            env="production",
            frontend_url="https://triadcare.example.com",
            allowed_origins="http://insecure.example.com"
        )
    assert "must use HTTPS scheme" in str(exc_info.value)


# ===========================================================================
# 9. Production Localhost Origins Rejected
# ===========================================================================
@pytest.mark.parametrize("insecure_url", [
    "https://localhost",
    "https://localhost:3000",
    "https://127.0.0.1:5173",
    "https://0.0.0.0:8000",
    "https://::1",
    "https://subdomain.localhost",
])
def test_production_cors_localhost_origins_rejected(insecure_url):
    """In production, localhost and loopback origins must be rejected."""
    with pytest.raises(RuntimeError) as exc_info:
        validate_cors_configuration(env="production", frontend_url=insecure_url)
    assert "cannot use localhost or loopback" in str(exc_info.value)


# ===========================================================================
# 10. Valid Production Origins Accepted
# ===========================================================================
def test_production_cors_valid_origins_accepted():
    """Valid HTTPS non-localhost origins in production are accepted and deduplicated."""
    origins = validate_cors_configuration(
        env="production",
        frontend_url="https://app.triadcare.org/",
        allowed_origins="https://portal.triadcare.org, https://admin.triadcare.org"
    )
    assert origins == [
        "https://app.triadcare.org",
        "https://portal.triadcare.org",
        "https://admin.triadcare.org"
    ]


# ===========================================================================
# 11. Development CORS Defaults To Localhost
# ===========================================================================
def test_development_cors_allows_localhost_defaults():
    """Development mode must permit local development server origins."""
    origins = validate_cors_configuration(env="development", frontend_url=None)
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins
    assert "http://localhost:3000" in origins


# ===========================================================================
# 12. Production Lifespan Aborts Startup on Invalid CORS
# ===========================================================================
def test_production_lifespan_startup_fails_on_invalid_cors(monkeypatch):
    """FastAPI startup lifespan must fail when production CORS is misconfigured."""
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.setenv("JWT_SECRET_KEY", "a" * 64)  # Valid JWT secret to isolate CORS check

    with pytest.raises(RuntimeError) as exc_info:
        with TestClient(app):
            pass
    assert "FRONTEND_URL must be explicitly set" in str(exc_info.value)


# ===========================================================================
# 13. JWT Secret Never Leaked In Exception Messages
# ===========================================================================
def test_auth_utils_secret_not_leaked_in_exception():
    """Exception messages must never leak the secret key value."""
    sensitive_placeholder = "secret"
    with pytest.raises(RuntimeError) as exc_info:
        validate_jwt_configuration(secret=sensitive_placeholder)

    msg = str(exc_info.value)
    assert "Insecure placeholder secret detected" in msg
    assert f"'{sensitive_placeholder}'" not in msg
    assert f'"{sensitive_placeholder}"' not in msg


# ===========================================================================
# 14. Refresh-Token Rotation and Replay Detection
# ===========================================================================
def test_refresh_token_rotation_and_replay_detection():
    """Verify refresh-token rotation produces single successor and replay revokes family."""
    client = TestClient(app)

    # 1. Login
    login_res = client.post("/api/auth/demo-login", json={"role": "caregiver"})
    assert login_res.status_code == 200
    token1 = login_res.cookies.get("refresh_token")
    csrf1 = login_res.json()["csrf_token"]
    assert token1 is not None

    headers1 = {"X-CSRF-Token": csrf1, "Origin": "http://localhost:5173"}
    cookies1 = {"refresh_token": token1, "csrf_token": csrf1}

    # 2. First rotation: must succeed
    rotate_res = client.post("/api/auth/refresh", headers=headers1, cookies=cookies1)
    assert rotate_res.status_code == 200
    token2 = rotate_res.cookies.get("refresh_token")
    csrf2 = rotate_res.json()["csrf_token"]
    assert token2 is not None
    assert token2 != token1

    # 3. Replay attack: Re-using token1 must return 401 and revoke the entire family
    replay_res = client.post("/api/auth/refresh", headers=headers1, cookies=cookies1)
    assert replay_res.status_code == 401

    # 4. Successor token2 must now also be rejected because its family was revoked
    headers2 = {"X-CSRF-Token": csrf2, "Origin": "http://localhost:5173"}
    cookies2 = {"refresh_token": token2, "csrf_token": csrf2}
    victim_res = client.post("/api/auth/refresh", headers=headers2, cookies=cookies2)
    assert victim_res.status_code == 401
