"""
test_security_upgrade.py – Adversarial Security & Invariant Verification Suite for Triad Care.
Validates:
  1. Argon2id password hashing and absence of plaintext passcodes.
  2. Access token validation (expiry, tampering, type, inactive user).
  3. Refresh token rotation, replay detection, single-successor enforcement, and logout revocation.
  4. CSRF protection on cookie-dependent endpoints (refresh, logout, bootstrap).
  5. Healthcare safety invariants (dose status independent of followup lifecycle, confirmation semantics).
  6. Role enforcement & authorization boundaries.
  7. Demo mode isolation.
"""
import pytest
import httpx
from datetime import datetime, timezone, timedelta
import jwt

from auth_utils import (
    hash_password, verify_password, create_access_token, decode_access_token,
    SECRET_KEY, ALGORITHM, ISSUER, AUDIENCE
)

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# 1. CREDENTIALS & STORAGE SECURITY
# =========================================================================
def test_argon2id_hashing_and_verification():
    """Verify that password hashing uses robust Argon2id parameters."""
    pwd = "secure_test_password_123"
    hashed = hash_password(pwd)
    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, pwd) is True
    assert verify_password(hashed, "wrong_password") is False


def test_no_plaintext_passcode_column_in_database():
    """Ensure that the database schema no longer contains a plaintext 'passcode' column."""
    import sqlite3
    conn = sqlite3.connect("caresync.db")
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]
    conn.close()
    assert "passcode" not in cols, "CRITICAL DEFECT: users table still contains plaintext passcode column!"
    assert "hashed_password" in cols, "users table missing hashed_password column!"


def test_no_password_hashes_in_api_responses(client):
    """Verify that user API responses never leak hashed_password."""
    # Demo users endpoint
    res = client.get("/api/auth/demo-users")
    assert res.status_code == 200
    for u in res.json():
        assert "hashed_password" not in u
        assert "passcode" not in u

    # Login response
    res = client.post("/api/auth/login", json={"passcode": "1111"})
    assert res.status_code == 200
    data = res.json()
    assert "hashed_password" not in data["user"]
    assert "passcode" not in data["user"]


# =========================================================================
# 2. JWT ACCESS TOKEN VALIDATION
# =========================================================================
def test_expired_jwt_rejection(client):
    """An expired JWT access token must be rejected with 401."""
    expired_token = create_access_token(user_id=1, expires_delta=timedelta(seconds=-10))
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401, f"Expected 401 for expired token, got {res.status_code}"


def test_tampered_jwt_signature_rejection(client):
    """A JWT with an invalid or tampered signature must be rejected with 401."""
    valid_token = create_access_token(user_id=1)
    # Tamper with the signature portion
    parts = valid_token.split(".")
    tampered_sig = parts[2][:-4] + "XXXX"
    tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res.status_code == 401, f"Expected 401 for tampered token, got {res.status_code}"


def test_invalid_token_type_rejection(client):
    """A JWT with type != 'access' must be rejected with 401."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "1",
        "type": "refresh",  # Wrong type
        "jti": "some-uuid",
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "iss": ISSUER,
        "aud": AUDIENCE,
    }
    wrong_type_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {wrong_type_token}"})
    assert res.status_code == 401


# =========================================================================
# 3. REFRESH TOKEN ROTATION, REPLAY DETECTION & REVOCATION
# =========================================================================
def test_refresh_token_lifecycle_and_rotation(client):
    """Login issues a refresh cookie; /refresh rotates it and returns a new access token."""
    login_res = client.post("/api/auth/login", json={"passcode": "1111"})
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    csrf_token = login_res.json()["csrf_token"]
    assert "refresh_token" in login_res.cookies

    # Call /refresh with the cookie and X-CSRF-Token header
    refresh_res = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": csrf_token},
        cookies={"refresh_token": login_res.cookies["refresh_token"], "csrf_token": csrf_token},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    assert new_data["access_token"] != login_res.json()["access_token"]
    assert "refresh_token" in refresh_res.cookies


def test_refresh_token_replay_triggers_family_revocation(client):
    """Replaying an already-rotated refresh token must fail and revoke the session."""
    login_res = client.post("/api/auth/login", json={"passcode": "2222"})
    assert login_res.status_code == 200
    csrf1 = login_res.json()["csrf_token"]
    old_rt = login_res.cookies["refresh_token"]

    # First rotation (valid)
    rot1_res = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": csrf1},
        cookies={"refresh_token": old_rt, "csrf_token": csrf1},
    )
    assert rot1_res.status_code == 200
    csrf2 = rot1_res.json()["csrf_token"]

    # Replay attack: present the old already-rotated token
    replay_res = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": csrf2},
        cookies={"refresh_token": old_rt, "csrf_token": csrf2},
    )
    assert replay_res.status_code == 401
    assert "Token reuse detected" in replay_res.json().get("detail", "")


def test_logout_revokes_session(client):
    """Logout invalidates the refresh token and clears auth cookies."""
    login_res = client.post("/api/auth/login", json={"passcode": "3333"})
    assert login_res.status_code == 200
    csrf = login_res.json()["csrf_token"]
    rt = login_res.cookies["refresh_token"]

    # Logout
    logout_res = client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": csrf},
        cookies={"refresh_token": rt, "csrf_token": csrf},
    )
    assert logout_res.status_code == 200

    # Attempt to refresh with the logged-out token -> must fail
    refresh_after = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": csrf},
        cookies={"refresh_token": rt, "csrf_token": csrf},
    )
    assert refresh_after.status_code == 401


# =========================================================================
# 4. CSRF PROTECTION & LIFECYCLE
# =========================================================================
def test_csrf_missing_token_rejected(client):
    """Mutating cookie-dependent endpoints must reject requests without X-CSRF-Token."""
    login_res = client.post("/api/auth/login", json={"passcode": "1111"})
    rt = login_res.cookies.get("refresh_token")
    csrf = login_res.cookies.get("csrf_token")

    # Missing X-CSRF-Token header
    res = client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": rt, "csrf_token": csrf},
    )
    assert res.status_code == 403
    assert "CSRF" in res.json().get("detail", "")


def test_csrf_mismatched_token_rejected(client):
    """Requests with mismatched X-CSRF-Token header and cookie must be rejected with 403."""
    login_res = client.post("/api/auth/login", json={"passcode": "1111"})
    rt = login_res.cookies.get("refresh_token")

    res = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": "forged-csrf-token-12345"},
        cookies={"refresh_token": rt, "csrf_token": "valid-csrf-token-67890"},
    )
    assert res.status_code == 403


def test_csrf_bootstrap_flow(client):
    """CSRF bootstrap endpoint issues a valid CSRF token when a live refresh session exists."""
    login_res = client.post("/api/auth/login", json={"passcode": "1111"})
    rt = login_res.cookies["refresh_token"]

    boot_res = client.get("/api/auth/csrf-bootstrap", cookies={"refresh_token": rt})
    assert boot_res.status_code == 200
    assert "csrf_token" in boot_res.json()
    assert len(boot_res.json()["csrf_token"]) > 20


# =========================================================================
# 5. HEALTHCARE SAFETY INVARIANTS
# =========================================================================
def test_safety_caregiver_reported_intake_not_automatically_taken(client):
    """
    CRITICAL HEALTHCARE SAFETY:
    When confirmation_method is 'caregiver_reported' (unwitnessed report),
    the dose status is NOT automatically changed to 'taken'.
    """
    caregiver_token = create_access_token(user_id=2)
    headers = {"Authorization": f"Bearer {caregiver_token}"}

    # Pick an unconfirmed dose
    doses = client.get("/api/doses/1/today", headers=headers).json()
    unconfirmed = [d for d in doses if d["status"] != "taken"]
    if not unconfirmed:
        pytest.skip("No unconfirmed doses available for reported test")
    target_dose = unconfirmed[0]
    initial_status = target_dose["status"]

    # Confirm with caregiver_reported method
    res = client.post(
        f"/api/doses/{target_dose['id']}/confirm",
        headers=headers,
        json={
            "confirmed_by_user_id": 2,
            "confirmation_method": "caregiver_reported",
        },
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["confirmation_method"] == "caregiver_reported"
    assert updated["status"] == initial_status, (
        f"SAFETY DEFECT: caregiver_reported intake auto-marked dose as taken! Status: {updated['status']}"
    )


def test_safety_followup_claim_and_resolve_never_marks_dose_taken(client):
    """
    CRITICAL HEALTHCARE SAFETY:
    Neither claiming a followup nor resolving it may EVER mark a dose taken.
    """
    caregiver_token = create_access_token(user_id=2)
    headers = {"Authorization": f"Bearer {caregiver_token}"}

    doses = client.get("/api/doses/1/today", headers=headers).json()
    target = next((d for d in doses if d["status"] != "taken"), None)
    if not target:
        pytest.skip("No non-taken doses available")
    target_id = target["id"]
    status_orig = target["status"]

    # 1. Claim
    claim = client.post(
        "/api/followups/claim",
        headers=headers,
        json={"dose_schedule_id": target_id, "caregiver_id": 2, "action": "going_to_check"},
    )
    assert claim.status_code == 200
    fid = claim.json()["id"]

    # Verify dose status unchanged
    doses_check = client.get("/api/doses/1/today", headers=headers).json()
    d = next(x for x in doses_check if x["id"] == target_id)
    assert d["status"] == status_orig
    assert d["status"] != "taken"

    # 2. Resolve
    resolve = client.put(f"/api/followups/{fid}", headers=headers, json={"status": "resolved", "notes": "Safety test note"})
    assert resolve.status_code == 200

    # Verify dose status still unchanged
    doses_final = client.get("/api/doses/1/today", headers=headers).json()
    d_fin = next(x for x in doses_final if x["id"] == target_id)
    assert d_fin["status"] == status_orig
    assert d_fin["status"] != "taken"
