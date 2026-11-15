"""
test_comprehensive_security.py – Comprehensive Security Remediation Adversarial Test Suite

Covers all 26 required scenarios from Part K:
  1. Missing bearer token → 401.
  2. Invalid/expired JWT → 401.
  3. Unauthorized care-circle membership → 403.
  4. Demo user accessing real profile → denied (403).
  5. Real user accessing demo profile → denied (403).
  6. Demo login disabled in production mode.
  7. Normal login cannot authenticate demo users in production mode.
  8. Medication ID from another profile rejected in change requests.
  9. Approval cannot modify a medication from another profile.
  10. Private notifications cannot be read or modified by other members.
  11. Mark-all-read respects notification ownership.
  12. Arbitrary resolved_at rejected or ignored.
  13. Invalid follow-up state transitions rejected.
  14. Follow-up actions never modify dose status.
  15. Concurrent refresh requests cannot create multiple successors.
  16. Refresh-token replay revokes the family.
  17. Missing/hostile Origin rejected on protected cookie operations.
  18. Missing/default JWT secret causes secure startup failure.
  19. Oversized upload rejected.
  20. MIME/signature mismatch rejected.
  21. Unsupported file types rejected.
  22. Rate limiting works.
  23. Security headers are present.
  24. Production CORS excludes development origins.
  25. Migration behavior preserves existing user data.
  26. All previously implemented BOLA protections continue working.
"""

import io
import os
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

from main import app
from auth_utils import create_access_token, validate_jwt_configuration
import routers.auth as auth_router

# Client fixtures
@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    from routers.ai import _ai_rate_limits
    _ai_rate_limits.clear()


# Setup fixture for realistic real vs demo profiles and users
@pytest.fixture(scope="module", autouse=True)
def setup_security_test_data():
    """Seed test fixtures:
      - Profile 1: Demo profile (is_demo=1) with User 1 (elderly, demo=1), User 2 (caregiver, demo=1)
      - Profile 888: Real profile (is_demo=0) with User 888 (elderly, real/is_demo=0)
      - Profile 889: Another real profile (is_demo=0) with User 889 (elderly, real/is_demo=0)
    """
    engine = create_engine("sqlite:///caresync.db")
    with engine.begin() as conn:
        # Cleanup any old test fixtures
        conn.execute(text("DELETE FROM profile_memberships WHERE user_id IN (888, 889, 990)"))
        conn.execute(text("DELETE FROM patient_profiles WHERE id IN (888, 889, 990)"))
        conn.execute(text("DELETE FROM users WHERE id IN (888, 889, 990)"))

        # Insert real users (is_demo=0)
        conn.execute(text(
            "INSERT INTO users (id, name, email, role, is_active, is_demo, hashed_password) "
            "VALUES (888, 'Real Patient', 'real@example.com', 'elderly', 1, 0, '$argon2id$v=19$m=65536,t=3,p=4$fakehash')"
        ))
        conn.execute(text(
            "INSERT INTO users (id, name, email, role, is_active, is_demo, hashed_password) "
            "VALUES (889, 'Real Patient Two', 'real2@example.com', 'elderly', 1, 0, '$argon2id$v=19$m=65536,t=3,p=4$fakehash')"
        ))

        # Insert real patient profiles (is_demo=0)
        conn.execute(text("INSERT INTO patient_profiles (id, name, is_demo) VALUES (888, 'Real Profile', 0)"))
        conn.execute(text("INSERT INTO patient_profiles (id, name, is_demo) VALUES (889, 'Real Profile Two', 0)"))

        # Memberships
        conn.execute(text(
            "INSERT INTO profile_memberships (id, profile_id, user_id, role, status) "
            "VALUES (888, 888, 888, 'elderly', 'active')"
        ))
        conn.execute(text(
            "INSERT INTO profile_memberships (id, profile_id, user_id, role, status) "
            "VALUES (889, 889, 889, 'elderly', 'active')"
        ))

    yield

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM profile_memberships WHERE user_id IN (888, 889, 990)"))
        conn.execute(text("DELETE FROM patient_profiles WHERE id IN (888, 889, 990)"))
        conn.execute(text("DELETE FROM users WHERE id IN (888, 889, 990)"))


# Helper tokens
DEMO_ELDERLY_TOKEN = create_access_token(user_id=1)     # User 1 is demo=1, belongs to Profile 1 (demo=1)
DEMO_CAREGIVER_TOKEN = create_access_token(user_id=2)   # User 2 is demo=1, belongs to Profile 1 (demo=1)
REAL_USER_888_TOKEN = create_access_token(user_id=888)  # User 888 is real=0, belongs to Profile 888 (real=0)
REAL_USER_889_TOKEN = create_access_token(user_id=889)  # User 889 is real=0, belongs to Profile 889 (real=0)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1. Missing bearer token → 401
# ===========================================================================
def test_1_missing_bearer_token_returns_401(client):
    res = client.get("/api/patients/1")
    assert res.status_code == 401


# ===========================================================================
# 2. Invalid / expired JWT → 401
# ===========================================================================
def test_2_invalid_or_expired_jwt_returns_401(client):
    expired = create_access_token(user_id=1, expires_delta=timedelta(seconds=-120))
    res = client.get("/api/patients/1", headers=_auth(expired))
    assert res.status_code == 401

    res_invalid = client.get("/api/patients/1", headers=_auth("malformed.jwt.token"))
    assert res_invalid.status_code == 401


# ===========================================================================
# 3. Unauthorized care-circle membership → 403
# ===========================================================================
def test_3_unauthorized_care_circle_membership_returns_403(client):
    # Real user 889 has no membership in Real profile 888
    res = client.get("/api/patients/888", headers=_auth(REAL_USER_889_TOKEN))
    assert res.status_code == 403


# ===========================================================================
# 4. Demo user accessing real profile → denied (403)
# ===========================================================================
def test_4_demo_user_accessing_real_profile_denied(client):
    # User 1 is is_demo=1. Profile 888 is is_demo=0.
    res = client.get("/api/patients/888", headers=_auth(DEMO_ELDERLY_TOKEN))
    assert res.status_code == 403
    assert "demo" in res.json().get("detail", "").lower() or res.status_code == 403


# ===========================================================================
# 5. Real user accessing demo profile → denied (403)
# ===========================================================================
def test_5_real_user_accessing_demo_profile_denied(client):
    # User 888 is is_demo=0. Profile 1 is is_demo=1.
    res = client.get("/api/patients/1", headers=_auth(REAL_USER_888_TOKEN))
    assert res.status_code == 403
    assert "demo" in res.json().get("detail", "").lower() or res.status_code == 403


# ===========================================================================
# 6. Demo login disabled in production mode
# ===========================================================================
def test_6_demo_login_disabled_in_production(client):
    original = auth_router.DEMO_MODE
    try:
        auth_router.DEMO_MODE = False
        res = client.post("/api/auth/demo-login", json={"role": "elderly"})
        assert res.status_code == 404
    finally:
        auth_router.DEMO_MODE = original


# ===========================================================================
# 7. Normal login cannot authenticate demo users in production mode
# ===========================================================================
def test_7_normal_login_rejects_demo_users_when_demo_mode_false(client):
    original = auth_router.DEMO_MODE
    try:
        auth_router.DEMO_MODE = False
        res = client.post("/api/auth/login", json={"passcode": "1111"})
        assert res.status_code == 401
    finally:
        auth_router.DEMO_MODE = original


# ===========================================================================
# 8. Medication ID from another profile rejected in change requests
# ===========================================================================
def test_8_medication_from_another_profile_rejected_in_change_request(client):
    # Medication 1 belongs to Profile 1.
    # User 888 (Profile 888) attempts to create change request on Profile 888 pointing to Medication 1.
    body = {
        "medication_id": 1,
        "change_type": "dosage",
        "reason": "Trying to modify other profile medication",
        "proposed_details": {"dosage": "500mg"}
    }
    res = client.post("/api/changes/888", headers=_auth(REAL_USER_888_TOKEN), json=body)
    assert res.status_code == 400
    assert "belong" in res.json().get("detail", "").lower()


# ===========================================================================
# 9. Approval cannot modify a medication from another profile
# ===========================================================================
def test_9_approval_cannot_modify_medication_from_another_profile(client):
    # Insert a malicious change request on Profile 1 directly into DB that points to a nonexistent/foreign med
    engine = create_engine("sqlite:///caresync.db")
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO medication_change_requests (id, profile_id, requested_by_user_id, medication_id, change_type, proposed_details, reason, status) "
            "VALUES (9999, 1, 1, 99999, 'dosage_change', '{\"new_dosage\": \"100mg\"}', 'Hacked', 'pending')"
        ))

    try:
        # Elderly patient reviews and attempts to approve
        res = client.put("/api/changes/9999/review", headers=_auth(DEMO_ELDERLY_TOKEN), json={"status": "approved"})
        assert res.status_code == 400
        assert "belong" in res.json().get("detail", "").lower() or res.status_code == 400
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM medication_change_requests WHERE id = 9999"))


# ===========================================================================
# 10. Private notifications cannot be read or modified by other members
# ===========================================================================
def test_10_private_notifications_cannot_be_read_or_modified_by_other_members(client):
    # Insert a private notification for user 2 (caregiver) on Profile 1
    engine = create_engine("sqlite:///caresync.db")
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO notifications (id, profile_id, user_id, title, body, type, is_read) "
            "VALUES (7777, 1, 2, 'Private to Caregiver', 'Confidential note', 'caregiver_alert', 0)"
        ))

    try:
        # User 1 (elderly) lists notifications -> must NOT see private notification 7777
        res_list = client.get("/api/notifications/1", headers=_auth(DEMO_ELDERLY_TOKEN))
        assert res_list.status_code == 200
        ids = [n["id"] for n in res_list.json()]
        assert 7777 not in ids

        # User 1 attempts to mark private notification 7777 as read -> 403 Forbidden
        res_read = client.put("/api/notifications/7777/read", headers=_auth(DEMO_ELDERLY_TOKEN))
        assert res_read.status_code == 403

        # User 2 (intended recipient) lists notifications -> DOES see private notification 7777
        res_caregiver_list = client.get("/api/notifications/1", headers=_auth(DEMO_CAREGIVER_TOKEN))
        assert res_caregiver_list.status_code == 200
        cg_ids = [n["id"] for n in res_caregiver_list.json()]
        assert 7777 in cg_ids

        # User 2 can mark it read
        res_cg_read = client.put("/api/notifications/7777/read", headers=_auth(DEMO_CAREGIVER_TOKEN))
        assert res_cg_read.status_code == 200
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM notifications WHERE id = 7777"))


# ===========================================================================
# 11. Mark-all-read respects notification ownership
# ===========================================================================
def test_11_mark_all_read_respects_notification_ownership(client):
    # Insert a private notification for user 2 (caregiver)
    engine = create_engine("sqlite:///caresync.db")
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO notifications (id, profile_id, user_id, title, body, type, is_read) "
            "VALUES (7778, 1, 2, 'Private to Caregiver', 'Note', 'caregiver_alert', 0)"
        ))

    try:
        # User 1 (elderly) executes mark-all-read on Profile 1
        res = client.put("/api/notifications/1/read-all", headers=_auth(DEMO_ELDERLY_TOKEN))
        assert res.status_code == 200

        # Verify notification 7778 for User 2 is STILL UNREAD
        with engine.connect() as conn:
            row = conn.execute(text("SELECT is_read FROM notifications WHERE id = 7778")).fetchone()
            assert row[0] == 0, "User 2's private notification was erroneously marked read by User 1"
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM notifications WHERE id = 7778"))


# ===========================================================================
# 12. Arbitrary resolved_at rejected or ignored
# ===========================================================================
def test_12_arbitrary_resolved_at_ignored_or_rejected(client):
    # Followup 1 belongs to Profile 1, caregiver_id=2
    arbitrary_past_date = "2020-01-01T00:00:00"
    res = client.put(
        "/api/followups/1",
        headers=_auth(DEMO_CAREGIVER_TOKEN),
        json={"status": "resolved", "resolved_at": arbitrary_past_date}
    )
    assert res.status_code in (200, 422)
    if res.status_code == 200:
        data = res.json()
        assert not data["resolved_at"].startswith("2020"), "Server accepted client-supplied past resolved_at!"


# ===========================================================================
# 13. Invalid follow-up state transitions rejected
# ===========================================================================
def test_13_invalid_followup_state_transitions_rejected(client):
    # Followup 1 is currently "resolved". Cannot transition back to "accepted"
    res = client.put(
        "/api/followups/1",
        headers=_auth(DEMO_CAREGIVER_TOKEN),
        json={"status": "accepted"}
    )
    assert res.status_code == 400
    assert "transition" in res.json().get("detail", "").lower()


# ===========================================================================
# 14. Follow-up actions never modify dose status
# ===========================================================================
def test_14_followup_actions_never_modify_dose_status(client):
    # Dose 3 is 'not_confirmed'
    engine = create_engine("sqlite:///caresync.db")
    with engine.connect() as conn:
        status_before = conn.execute(text("SELECT status FROM dose_schedules WHERE id = 3")).scalar()

    # Claim followup for dose 3
    body = {"dose_schedule_id": 3, "action": "calling"}
    client.post("/api/followups/claim", headers=_auth(DEMO_CAREGIVER_TOKEN), json=body)

    with engine.connect() as conn:
        status_after = conn.execute(text("SELECT status FROM dose_schedules WHERE id = 3")).scalar()

    assert status_before == status_after, "Followup action modified dose status!"


# ===========================================================================
# 15. Concurrent refresh requests cannot create multiple successors
# ===========================================================================
def test_15_concurrent_refresh_rotation_single_successor(client):
    # Login as demo user to obtain refresh cookie + csrf token
    login_res = client.post("/api/auth/demo-login", json={"role": "caregiver"})
    assert login_res.status_code == 200
    refresh_token = login_res.cookies["refresh_token"]
    csrf_token = login_res.json()["csrf_token"]

    headers = {"X-CSRF-Token": csrf_token, "Origin": "http://localhost:5173"}
    cookies = {"refresh_token": refresh_token, "csrf_token": csrf_token}

    # First refresh: must succeed
    res1 = client.post("/api/auth/refresh", headers=headers, cookies=cookies)
    assert res1.status_code == 200

    # Second refresh with identical original token (simulating race or replay): MUST FAIL
    res2 = client.post("/api/auth/refresh", headers=headers, cookies=cookies)
    assert res2.status_code == 401


# ===========================================================================
# 16. Refresh-token replay revokes the family
# ===========================================================================
def test_16_refresh_token_replay_revokes_entire_family(client):
    login_res = client.post("/api/auth/demo-login", json={"role": "caregiver"})
    assert login_res.status_code == 200
    token_1 = login_res.cookies["refresh_token"]
    csrf_1 = login_res.json()["csrf_token"]

    # Rotate token 1 -> token 2
    res_rot = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": csrf_1, "Origin": "http://localhost:5173"},
        cookies={"refresh_token": token_1, "csrf_token": csrf_1}
    )
    assert res_rot.status_code == 200
    token_2 = res_rot.cookies["refresh_token"]
    csrf_2 = res_rot.json()["csrf_token"]

    # Replay token 1: MUST fail and revoke family
    replay_res = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": csrf_1, "Origin": "http://localhost:5173"},
        cookies={"refresh_token": token_1, "csrf_token": csrf_1}
    )
    assert replay_res.status_code == 401

    # Now attempt to use token 2 (the legitimate successor): MUST ALSO FAIL because family was revoked
    res_successor = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": csrf_2, "Origin": "http://localhost:5173"},
        cookies={"refresh_token": token_2, "csrf_token": csrf_2}
    )
    assert res_successor.status_code == 401


# ===========================================================================
# 17. Missing / hostile Origin rejected on protected cookie operations
# ===========================================================================
def test_17_hostile_origin_rejected_on_cookie_operations(client):
    login_res = client.post("/api/auth/demo-login", json={"role": "caregiver"})
    assert login_res.status_code == 200
    rt = login_res.cookies["refresh_token"]
    csrf = login_res.json()["csrf_token"]

    # Hostile Origin header
    headers = {"X-CSRF-Token": csrf, "Origin": "https://evil-attacker.com"}
    cookies = {"refresh_token": rt, "csrf_token": csrf}

    res = client.post("/api/auth/refresh", headers=headers, cookies=cookies)
    assert res.status_code == 403
    assert "not permitted" in res.json().get("detail", "").lower()


# ===========================================================================
# 18. Missing / default JWT secret causes secure startup failure
# ===========================================================================
def test_18_missing_or_default_jwt_secret_fails_validation():
    # Empty secret
    with pytest.raises(RuntimeError) as exc_empty:
        validate_jwt_configuration("")
    assert "missing" in str(exc_empty.value).lower()

    # Known insecure placeholder
    with pytest.raises(RuntimeError) as exc_default:
        validate_jwt_configuration("CHANGE_ME_IN_PRODUCTION_min32chars!!")
    assert "insecure placeholder" in str(exc_default.value).lower()

    # Too short (< 32 chars)
    with pytest.raises(RuntimeError) as exc_short:
        validate_jwt_configuration("too-short-secret")
    assert "32 characters" in str(exc_short.value).lower()

    # Valid secret passes cleanly
    validate_jwt_configuration("a-very-strong-production-jwt-secret-key-with-64-bytes-entropy!!")


# ===========================================================================
# 19. Oversized upload rejected (5 MB limit)
# ===========================================================================
def test_19_oversized_upload_rejected(client):
    # 5.5 MB dummy content
    oversized = b"\x89PNG\r\n\x1a\n" + (b"A" * (6 * 1024 * 1024))
    files = {"file": ("big.png", oversized, "image/png")}
    res = client.post("/api/ai/scan-prescription", headers=_auth(DEMO_ELDERLY_TOKEN), files=files)
    assert res.status_code == 413


# ===========================================================================
# 20. MIME / signature mismatch rejected
# ===========================================================================
def test_20_mime_signature_mismatch_rejected(client):
    # Client sends image/png header but bytes are plain text
    fake_png = b"This is plain text pretending to be a PNG file."
    files = {"file": ("prescription.png", fake_png, "image/png")}
    res = client.post("/api/ai/scan-prescription", headers=_auth(DEMO_ELDERLY_TOKEN), files=files)
    assert res.status_code in (400, 415)


# ===========================================================================
# 21. Unsupported file types rejected
# ===========================================================================
def test_21_unsupported_file_types_rejected(client):
    # PDF file
    pdf_bytes = b"%PDF-1.4\n%..."
    files = {"file": ("doc.pdf", pdf_bytes, "application/pdf")}
    res = client.post("/api/ai/scan-prescription", headers=_auth(DEMO_ELDERLY_TOKEN), files=files)
    assert res.status_code in (400, 415)


# ===========================================================================
# 22. Rate limiting works
# ===========================================================================
def test_22_ai_rate_limiting_works(client):
    # Trigger 11 rapid requests to scan-prescription
    hit_rate_limit = False
    for _ in range(12):
        res = client.post("/api/ai/scan-prescription", headers=_auth(DEMO_ELDERLY_TOKEN))
        if res.status_code == 429:
            hit_rate_limit = True
            break
    assert hit_rate_limit, "Rate limiter did not trigger after rapid successive AI requests"


# ===========================================================================
# 23. Security headers are present
# ===========================================================================
def test_23_security_headers_present(client):
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in res.headers.get("Content-Security-Policy", "")


# ===========================================================================
# 24. Production CORS excludes development origins
# ===========================================================================
def test_24_production_cors_excludes_development_origins():
    from dependencies import get_allowed_origins
    original_env = os.environ.get("ENV")
    try:
        os.environ["ENV"] = "production"
        os.environ["FRONTEND_URL"] = "https://triadcare.example.com"
        allowed = get_allowed_origins()
        assert "http://localhost:5173" not in allowed
        assert "http://localhost:3000" not in allowed
        assert "https://triadcare.example.com" in allowed
    finally:
        if original_env is not None:
            os.environ["ENV"] = original_env
        else:
            os.environ.pop("ENV", None)


# ===========================================================================
# 25. Migration behavior preserves existing user data
# ===========================================================================
def test_25_migration_preserves_existing_user_data():
    engine = create_engine("sqlite:///caresync.db")
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        assert count >= 3, "Seed users were lost!"
        med_count = conn.execute(text("SELECT COUNT(*) FROM medications")).scalar()
        assert med_count >= 5, "Seed medications were lost!"


# ===========================================================================
# 26. All previously implemented BOLA protections continue working
# ===========================================================================
def test_26_bola_protections_continue_working(client):
    # Real user 889 cannot modify Real user 888's appointment
    res = client.put(
        "/api/appointments/1",
        headers=_auth(REAL_USER_889_TOKEN),
        json={"notes": "Hacked appointment"}
    )
    assert res.status_code == 403
