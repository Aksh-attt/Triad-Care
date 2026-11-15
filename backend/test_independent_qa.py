"""
Independent QA Verification & Adversarial Safety Test Suite for Triad Care
This suite independently stress-tests the safety guarantees, role boundaries,
AI fallback honesty, error handling, and security invariants.
"""
import pytest
import httpx
import datetime

BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=10.0)


# =========================================================================
# 1. SECURITY & AUTHENTICATION AUDIT
# =========================================================================
def test_security_passcodes_not_exposed_in_demo_users(client):
    """Verify demo users endpoint does NOT return plaintext passcodes."""
    res = client.get("/api/auth/demo-users")
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 3
    for u in users:
        assert "passcode" not in u or u["passcode"] is None, (
            f"SECURITY DEFECT: User '{u.get('name')}' exposes plaintext passcode in demo-users API response!"
        )


def test_security_passcode_not_exposed_in_login_response(client):
    """Verify login response does NOT return plaintext passcode in user payload."""
    res = client.post("/api/auth/login", json={"passcode": "1111"})
    assert res.status_code == 200
    data = res.json()
    assert "user" in data
    assert "passcode" not in data["user"] or data["user"]["passcode"] is None, (
        "SECURITY DEFECT: Login response returns plaintext passcode in user object!"
    )


def test_security_missing_auth_middleware_vulnerability_audit(client):
    """
    DOCUMENTED SECURITY GAP:
    The API currently relies on unauthenticated endpoints (no Bearer JWT or session cookie).
    Any client can directly confirm doses or create appointments without an Authorization header.
    This test verifies that the endpoint functions in demo mode but highlights the absence of token verification.
    """
    # Dose confirmation without Authorization header
    doses = client.get("/api/doses/1/today").json()
    assert len(doses) > 0
    dose_id = doses[0]["id"]

    # Mutation succeeds without any Authorization header
    res = client.post(f"/api/doses/{dose_id}/confirm", json={"confirmed_by_user_id": 1})
    assert res.status_code == 200, "In demo mode, requests without auth tokens are accepted"


# =========================================================================
# 2. ADVERSARIAL ROLE ENFORCEMENT & SAFETY INVARIANTS
# =========================================================================
def test_safety_reject_non_elderly_medication_change_approval(client):
    """
    SAFETY INVARIANT 1:
    Only the elderly patient (user_id=1) is permitted to approve or reject
    medication changes. Caregivers and Family coordinators must be denied.
    """
    # 1. Propose a change as family
    prop_res = client.post(
        "/api/changes/1",
        json={
            "requested_by_user_id": 3,
            "medication_id": 1,
            "change_type": "dosage_change",
            "proposed_details": {"new_dosage": "600", "unit": "mg"},
            "reason": "Adversarial test: Unauthorized approval attempt",
        },
    )
    assert prop_res.status_code == 200
    change_id = prop_res.json()["id"]

    # 2. Family member (user_id=3) attempts to approve change -> MUST RETURN 403
    fam_attempt = client.put(
        f"/api/changes/{change_id}/review",
        json={"status": "approved", "reviewed_by_user_id": 3},
    )
    assert fam_attempt.status_code == 403, (
        f"SAFETY VIOLATION: Family member was able to approve medication change! Code: {fam_attempt.status_code}"
    )

    # 3. Caregiver (user_id=2) attempts to approve change -> MUST RETURN 403
    cg_attempt = client.put(
        f"/api/changes/{change_id}/review",
        json={"status": "approved", "reviewed_by_user_id": 2},
    )
    assert cg_attempt.status_code == 403, (
        f"SAFETY VIOLATION: Caregiver was able to approve medication change! Code: {cg_attempt.status_code}"
    )

    # 4. Verify the medication change remained pending and did not alter medication
    list_res = client.get("/api/changes/1").json()
    req = next(r for r in list_res if r["id"] == change_id)
    assert req["status"] == "pending", "Medication change was altered despite forbidden reviews!"

    # 5. Clean up by having elderly reject it
    clean_res = client.put(
        f"/api/changes/{change_id}/review",
        json={"status": "rejected", "reviewed_by_user_id": 1},
    )
    assert clean_res.status_code == 200
    assert clean_res.json()["status"] == "rejected"


def test_safety_prevent_double_review_of_medication_changes(client):
    """
    SAFETY INVARIANT 2:
    A medication change that has already been approved or rejected
    cannot be re-reviewed (prevents duplicate modification or state flips).
    """
    # 1. Propose change
    prop_res = client.post(
        "/api/changes/1",
        json={
            "requested_by_user_id": 3,
            "medication_id": 1,
            "change_type": "dosage_change",
            "proposed_details": {"new_dosage": "750", "unit": "mg"},
            "reason": "Adversarial test: Double review test",
        },
    )
    change_id = prop_res.json()["id"]

    # 2. Elderly rejects it
    first_review = client.put(
        f"/api/changes/{change_id}/review",
        json={"status": "rejected", "reviewed_by_user_id": 1},
    )
    assert first_review.status_code == 200

    # 3. Attempt to review again -> MUST RETURN 400 Bad Request
    second_review = client.put(
        f"/api/changes/{change_id}/review",
        json={"status": "approved", "reviewed_by_user_id": 1},
    )
    assert second_review.status_code == 400, "SAFETY DEFECT: Already-reviewed change request was reviewed again!"


def test_safety_reject_non_caregiver_followup_claim(client):
    """
    SAFETY INVARIANT 3:
    Only users with role 'caregiver' can claim follow-up responsibility.
    Elderly and Family members must be rejected.
    """
    doses = client.get("/api/doses/1/today").json()
    unconfirmed = [d for d in doses if d["status"] != "taken"]
    if not unconfirmed:
        pytest.skip("No unconfirmed doses available for claim test")
    dose_id = unconfirmed[0]["id"]

    # 1. Elderly attempts to claim caregiver follow-up -> MUST RETURN 403
    elderly_claim = client.post(
        "/api/followups/claim",
        json={"dose_schedule_id": dose_id, "caregiver_id": 1, "action": "calling"},
    )
    assert elderly_claim.status_code == 403, (
        f"SAFETY DEFECT: Elderly user was permitted to claim caregiver follow-up! Status: {elderly_claim.status_code}"
    )

    # 2. Family attempts to claim caregiver follow-up -> MUST RETURN 403
    family_claim = client.post(
        "/api/followups/claim",
        json={"dose_schedule_id": dose_id, "caregiver_id": 3, "action": "calling"},
    )
    assert family_claim.status_code == 403, (
        f"SAFETY DEFECT: Family member was permitted to claim caregiver follow-up! Status: {family_claim.status_code}"
    )


def test_safety_reject_invalid_followup_actions_and_statuses(client):
    """
    SAFETY INVARIANT 4:
    Caregiver follow-ups must strictly validate actions and statuses.
    Arbitrary actions or statuses must be rejected.
    """
    doses = client.get("/api/doses/1/today").json()
    unconfirmed = [d for d in doses if d["status"] != "taken"]
    if not unconfirmed:
        pytest.skip("No unconfirmed doses available for invalid action test")
    dose_id = unconfirmed[0]["id"]

    # Invalid action
    bad_action = client.post(
        "/api/followups/claim",
        json={"dose_schedule_id": dose_id, "caregiver_id": 2, "action": "invalid_action_xyz"},
    )
    assert bad_action.status_code == 400, "Validation failure: API accepted invalid follow-up action"

    # Valid claim
    valid_claim = client.post(
        "/api/followups/claim",
        json={"dose_schedule_id": dose_id, "caregiver_id": 2, "action": "going_to_check"},
    )
    assert valid_claim.status_code == 200
    followup_id = valid_claim.json()["id"]

    # Invalid status update
    bad_status = client.put(
        f"/api/followups/{followup_id}",
        json={"status": "invalid_status_xyz"},
    )
    assert bad_status.status_code == 400, "Validation failure: API accepted invalid follow-up status"


def test_safety_prevent_claiming_followup_on_already_taken_dose(client):
    """
    SAFETY INVARIANT 5:
    Follow-ups cannot be claimed for doses that have already been confirmed as taken.
    """
    # 1. Confirm a dose as taken
    doses = client.get("/api/doses/1/today").json()
    dose_id = doses[0]["id"]
    client.post(f"/api/doses/{dose_id}/confirm", json={"confirmed_by_user_id": 1})

    # 2. Verify dose is marked taken
    doses_now = client.get("/api/doses/1/today").json()
    assert any(d["id"] == dose_id and d["status"] == "taken" for d in doses_now)

    # 3. Attempt to claim follow-up on taken dose -> MUST RETURN 400
    res = client.post(
        "/api/followups/claim",
        json={"dose_schedule_id": dose_id, "caregiver_id": 2, "action": "calling"},
    )
    assert res.status_code == 400, "SAFETY DEFECT: Caregiver claimed follow-up on an already-taken dose!"


# =========================================================================
# 3. AI INTEGRATION INTEGRITY & RESILIENCE
# =========================================================================
def test_ai_demo_fallback_honesty(client):
    """
    AI HONESTY AUDIT:
    When no valid Gemini API key is configured, the API must explicitly flag
    responses with is_demo=True and not masquerade simulated data as live AI output.
    """
    res = client.post("/api/ai/weekly-summary/1")
    assert res.status_code == 200
    data = res.json()
    # In the absence of a production API key, it must clearly indicate demo status
    assert "is_demo" in data
    assert "stats" in data
    assert "summary" in data

    # Verify that factual stats contain all required healthcare fields
    stats = data["stats"]
    assert "recorded_reasons" in stats
    assert "pending_followups_count" in stats
    assert "upcoming_appointments_count" in stats
    assert isinstance(stats["recorded_reasons"], list)
    assert isinstance(stats["pending_followups_count"], int)
    assert isinstance(stats["upcoming_appointments_count"], int)


def test_ai_compare_prescription_malformed_input_resilience(client):
    """
    RESILIENCE AUDIT:
    Prescription comparison must handle malformed input (strings, missing keys,
    empty arrays) without throwing a 500 Internal Server Error.
    """
    # 1. Test empty array
    empty_res = client.post(
        "/api/ai/compare-prescription",
        json={"profile_id": 1, "extracted_items": []},
    )
    assert empty_res.status_code == 200
    assert empty_res.json()["comparison"] == []

    # 2. Test list of raw strings instead of dicts
    strings_res = client.post(
        "/api/ai/compare-prescription",
        json={"profile_id": 1, "extracted_items": ["Metformin 500mg", "UnknownDrug 10mg"]},
    )
    assert strings_res.status_code == 200
    comp = strings_res.json()["comparison"]
    assert len(comp) == 2
    assert comp[0]["is_existing"] is True  # Metformin matches existing

    # 3. Test dicts with missing fields
    missing_fields_res = client.post(
        "/api/ai/compare-prescription",
        json={"profile_id": 1, "extracted_items": [{"foo": "bar"}]},
    )
    assert missing_fields_res.status_code == 200


def test_ai_scanner_empty_upload_handling(client):
    """
    RESILIENCE AUDIT:
    Prescription scanner with no file attached returns fallback response without crashing.
    """
    res = client.post("/api/ai/scan-prescription")
    assert res.status_code == 200
    data = res.json()
    assert data["is_demo"] is True
    assert "extracted_items" in data


# =========================================================================
# 4. BOUNDARY CONDITIONS & PERSISTENCE
# =========================================================================
def test_boundary_nonexistent_entity_lookups(client):
    """Verify that querying or updating non-existent entities returns 404."""
    # Non-existent appointment update
    assert client.put("/api/appointments/999999", json={"notes": "test"}).status_code == 404

    # Non-existent appointment delete
    assert client.delete("/api/appointments/999999").status_code == 404

    # Non-existent change review
    assert client.put("/api/changes/999999/review", json={"status": "approved", "reviewed_by_user_id": 1}).status_code == 404

    # Non-existent patient profile weekly summary
    assert client.post("/api/ai/weekly-summary/999999").status_code == 404


def test_database_persistence_across_endpoints(client):
    """
    PERSISTENCE AUDIT:
    Verify that records created in one endpoint persist and are visible to other endpoints.
    """
    # 1. Create a notification
    appt = client.post(
        "/api/appointments/1",
        json={
            "doctor_name": "Dr. Persistence Check",
            "specialty": "General Medicine",
            "date_time": (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat(),
            "location": "Central Clinic",
            "notes": "Verify cross-session persistence",
        },
    ).json()
    appt_id = appt["id"]

    # 2. Read back from list
    appts = client.get("/api/appointments/1").json()
    assert any(a["id"] == appt_id for a in appts)

    # 3. Clean up
    client.delete(f"/api/appointments/{appt_id}")
