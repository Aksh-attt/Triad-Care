"""
test_stage1_auth.py – Stage 1 Security Remediation: Adversarial Authentication & Authorization Tests

Covers every protected router for:
  1. Missing Authorization header → 401
  2. Invalid / expired token → 401
  3. Authenticated user from another care circle → 403 (Care Circle Isolation)
  4. Cross-profile individual resource ID cannot be read or modified → 403 (BOLA/IDOR protection)
  5. Client-supplied identity fields (confirmed_by_user_id, caregiver_id, requested_by_user_id,
     reviewed_by_user_id) are ignored — server derives them exclusively from current_user.id.

Setup:
  - Users 1/2/3 belong to Profile 1 (seeded in caresync.db).
  - User 990 (Stranger) belongs to Profile 990 (temporary care circle).
  - Valid tokens for Users 1 (elderly), 2 (caregiver), 3 (family), 990 (stranger).
  - Expired and malformed tokens.
"""

import pytest
from datetime import timedelta
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

from main import app
from auth_utils import create_access_token

# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------
ELDERLY_TOKEN   = create_access_token(user_id=1)    # Meera – elderly (Profile 1)
CAREGIVER_TOKEN = create_access_token(user_id=2)    # Riya  – caregiver (Profile 1)
FAMILY_TOKEN    = create_access_token(user_id=3)    # Arjun – family (Profile 1)
STRANGER_TOKEN  = create_access_token(user_id=990)  # Stranger – elderly (Profile 990)

EXPIRED_TOKEN   = create_access_token(user_id=1, expires_delta=timedelta(seconds=-60))
INVALID_TOKEN   = "not.a.valid.jwt.token"
NONEXISTENT_USER_TOKEN = create_access_token(user_id=99999)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_second_care_circle():
    """Seed an isolated second care circle (User 990, Profile 990, Membership 990).
    Cleaned up at the end of the test module to keep caresync.db intact.
    """
    sync_engine = create_engine("sqlite:///caresync.db")
    with sync_engine.begin() as conn:
        conn.execute(text("DELETE FROM profile_memberships WHERE user_id = 990"))
        conn.execute(text("DELETE FROM patient_profiles WHERE id = 990"))
        conn.execute(text("DELETE FROM users WHERE id = 990"))

        conn.execute(text(
            "INSERT INTO users (id, name, email, role, is_active, is_demo) "
            "VALUES (990, 'Stranger User', 'stranger@example.com', 'elderly', 1, 0)"
        ))
        conn.execute(text(
            "INSERT INTO patient_profiles (id, name) VALUES (990, 'Stranger Patient')"
        ))
        conn.execute(text(
            "INSERT INTO profile_memberships (id, profile_id, user_id, role, status) "
            "VALUES (990, 990, 990, 'elderly', 'active')"
        ))
    yield
    with sync_engine.begin() as conn:
        conn.execute(text("DELETE FROM profile_memberships WHERE user_id = 990"))
        conn.execute(text("DELETE FROM patient_profiles WHERE id = 990"))
        conn.execute(text("DELETE FROM users WHERE id = 990"))


# ===========================================================================
# 1. PATIENTS ROUTER  /api/patients
# ===========================================================================

class TestPatientsAuth:

    def test_get_patient_no_auth(self, client):
        res = client.get("/api/patients/1")
        assert res.status_code == 401

    def test_get_patient_expired_token(self, client):
        res = client.get("/api/patients/1", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_get_patient_invalid_token(self, client):
        res = client.get("/api/patients/1", headers=_auth(INVALID_TOKEN))
        assert res.status_code == 401

    def test_get_patient_other_care_circle_forbidden(self, client):
        # User 990 from another care circle accessing Profile 1
        res = client.get("/api/patients/1", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_get_patient_valid_member(self, client):
        res = client.get("/api/patients/1", headers=_auth(ELDERLY_TOKEN))
        assert res.status_code == 200

    def test_update_patient_no_auth(self, client):
        res = client.put("/api/patients/1", json={"name": "New Name"})
        assert res.status_code == 401

    def test_update_patient_expired_token(self, client):
        res = client.put("/api/patients/1", headers=_auth(EXPIRED_TOKEN), json={"name": "New Name"})
        assert res.status_code == 401

    def test_update_patient_other_care_circle_forbidden(self, client):
        res = client.put("/api/patients/1", headers=_auth(STRANGER_TOKEN), json={"name": "New Name"})
        assert res.status_code == 403

    def test_update_patient_caregiver_forbidden(self, client):
        # Only elderly role permitted to edit patient profile
        res = client.put("/api/patients/1", headers=_auth(CAREGIVER_TOKEN), json={"name": "New Name"})
        assert res.status_code == 403

    def test_update_patient_family_forbidden(self, client):
        res = client.put("/api/patients/1", headers=_auth(FAMILY_TOKEN), json={"name": "New Name"})
        assert res.status_code == 403

    def test_get_members_no_auth(self, client):
        res = client.get("/api/patients/1/members")
        assert res.status_code == 401

    def test_get_members_expired_token(self, client):
        res = client.get("/api/patients/1/members", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_get_members_other_care_circle_forbidden(self, client):
        res = client.get("/api/patients/1/members", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403


# ===========================================================================
# 2. MEDICATIONS ROUTER  /api/medications
# ===========================================================================

class TestMedicationsAuth:

    def test_list_medications_no_auth(self, client):
        res = client.get("/api/medications/1")
        assert res.status_code == 401

    def test_list_medications_expired_token(self, client):
        res = client.get("/api/medications/1", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_list_medications_other_care_circle_forbidden(self, client):
        res = client.get("/api/medications/1", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_list_medications_valid(self, client):
        res = client.get("/api/medications/1", headers=_auth(ELDERLY_TOKEN))
        assert res.status_code == 200

    def test_add_medication_no_auth(self, client):
        body = {
            "name": "Test Med", "dosage": "10mg", "unit": "mg",
            "frequency": "daily", "start_date": "2026-01-01", "timing_slots": ["morning"]
        }
        res = client.post("/api/medications/1", json=body)
        assert res.status_code == 401

    def test_add_medication_other_care_circle_forbidden(self, client):
        body = {
            "name": "Test Med", "dosage": "10mg", "unit": "mg",
            "frequency": "daily", "start_date": "2026-01-01", "timing_slots": ["morning"]
        }
        res = client.post("/api/medications/1", headers=_auth(STRANGER_TOKEN), json=body)
        assert res.status_code == 403

    def test_add_medication_caregiver_forbidden(self, client):
        # Direct active medication addition is elderly-only (sovereignty rule)
        body = {
            "name": "Test Med", "dosage": "10mg", "unit": "mg",
            "frequency": "daily", "start_date": "2026-01-01", "timing_slots": ["morning"]
        }
        res = client.post("/api/medications/1", headers=_auth(CAREGIVER_TOKEN), json=body)
        assert res.status_code == 403

    def test_add_medication_family_forbidden(self, client):
        body = {
            "name": "Test Med", "dosage": "10mg", "unit": "mg",
            "frequency": "daily", "start_date": "2026-01-01", "timing_slots": ["morning"]
        }
        res = client.post("/api/medications/1", headers=_auth(FAMILY_TOKEN), json=body)
        assert res.status_code == 403

    def test_update_medication_no_auth(self, client):
        res = client.put("/api/medications/1", json={"dosage": "20mg"})
        assert res.status_code == 401

    def test_update_medication_expired_token(self, client):
        res = client.put("/api/medications/1", headers=_auth(EXPIRED_TOKEN), json={"dosage": "20mg"})
        assert res.status_code == 401

    def test_update_medication_cross_profile_bola_forbidden(self, client):
        # Medication 1 belongs to Profile 1. User 990 belongs to Profile 990.
        res = client.put("/api/medications/1", headers=_auth(STRANGER_TOKEN), json={"dosage": "20mg"})
        assert res.status_code == 403

    def test_update_medication_caregiver_forbidden(self, client):
        res = client.put("/api/medications/1", headers=_auth(CAREGIVER_TOKEN), json={"dosage": "20mg"})
        assert res.status_code == 403

    def test_delete_medication_no_auth(self, client):
        res = client.delete("/api/medications/1")
        assert res.status_code == 401

    def test_delete_medication_cross_profile_bola_forbidden(self, client):
        res = client.delete("/api/medications/1", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_delete_medication_caregiver_forbidden(self, client):
        res = client.delete("/api/medications/1", headers=_auth(CAREGIVER_TOKEN))
        assert res.status_code == 403

    def test_schedule_no_auth(self, client):
        res = client.get("/api/medications/1/schedule/today")
        assert res.status_code == 401

    def test_schedule_expired_token(self, client):
        res = client.get("/api/medications/1/schedule/today", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_schedule_other_care_circle_forbidden(self, client):
        res = client.get("/api/medications/1/schedule/today", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403


# ===========================================================================
# 3. DOSES ROUTER  /api/doses
# ===========================================================================

class TestDosesAuth:

    def test_list_doses_today_no_auth(self, client):
        res = client.get("/api/doses/1/today")
        assert res.status_code == 401

    def test_list_doses_today_expired_token(self, client):
        res = client.get("/api/doses/1/today", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_list_doses_today_other_care_circle_forbidden(self, client):
        res = client.get("/api/doses/1/today", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_confirm_dose_no_auth(self, client):
        res = client.post("/api/doses/2/confirm", json={"confirmation_method": "patient_confirmed"})
        assert res.status_code == 401

    def test_confirm_dose_expired_token(self, client):
        res = client.post("/api/doses/2/confirm", headers=_auth(EXPIRED_TOKEN), json={})
        assert res.status_code == 401

    def test_confirm_dose_cross_profile_bola_forbidden(self, client):
        # Dose 2 belongs to Profile 1. Stranger user cannot confirm it.
        res = client.post("/api/doses/2/confirm", headers=_auth(STRANGER_TOKEN), json={})
        assert res.status_code == 403

    def test_confirm_dose_family_forbidden(self, client):
        res = client.post("/api/doses/2/confirm", headers=_auth(FAMILY_TOKEN), json={})
        assert res.status_code == 403

    def test_confirm_dose_identity_field_ignored(self, client):
        """Client sends confirmed_by_user_id=3 (family) in body, but auth is caregiver (user_id=2).
        Server ignores body and uses user_id=2 from JWT.
        """
        body = {"confirmed_by_user_id": 3, "confirmation_method": "caregiver_observed"}
        res = client.post("/api/doses/2/confirm", headers=_auth(CAREGIVER_TOKEN), json=body)
        assert res.status_code in (200, 400, 409)
        if res.status_code == 200:
            data = res.json()
            assert data.get("confirmed_by_user_id") == 2

    def test_record_reason_no_auth(self, client):
        res = client.post("/api/doses/3/reason", json={"reason": "felt dizzy"})
        assert res.status_code == 401

    def test_record_reason_cross_profile_bola_forbidden(self, client):
        res = client.post("/api/doses/3/reason", headers=_auth(STRANGER_TOKEN), json={"reason": "felt dizzy"})
        assert res.status_code == 403

    def test_record_reason_family_forbidden(self, client):
        res = client.post("/api/doses/3/reason", headers=_auth(FAMILY_TOKEN), json={"reason": "felt dizzy"})
        assert res.status_code == 403

    def test_dose_history_no_auth(self, client):
        res = client.get("/api/doses/1/history")
        assert res.status_code == 401

    def test_dose_history_expired_token(self, client):
        res = client.get("/api/doses/1/history", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_dose_history_other_care_circle_forbidden(self, client):
        res = client.get("/api/doses/1/history", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403


# ===========================================================================
# 4. APPOINTMENTS ROUTER  /api/appointments
# ===========================================================================

class TestAppointmentsAuth:

    def test_list_appointments_no_auth(self, client):
        res = client.get("/api/appointments/1")
        assert res.status_code == 401

    def test_list_appointments_expired_token(self, client):
        res = client.get("/api/appointments/1", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_list_appointments_other_care_circle_forbidden(self, client):
        res = client.get("/api/appointments/1", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_list_appointments_valid(self, client):
        res = client.get("/api/appointments/1", headers=_auth(ELDERLY_TOKEN))
        assert res.status_code == 200

    def test_add_appointment_no_auth(self, client):
        body = {
            "doctor_name": "Dr. Sharma", "specialty": "Cardiology",
            "date_time": "2026-12-01T10:00:00", "location": "City Clinic"
        }
        res = client.post("/api/appointments/1", json=body)
        assert res.status_code == 401

    def test_add_appointment_expired_token(self, client):
        body = {
            "doctor_name": "Dr. Sharma", "specialty": "Cardiology",
            "date_time": "2026-12-01T10:00:00", "location": "City Clinic"
        }
        res = client.post("/api/appointments/1", headers=_auth(EXPIRED_TOKEN), json=body)
        assert res.status_code == 401

    def test_add_appointment_other_care_circle_forbidden(self, client):
        body = {
            "doctor_name": "Dr. Sharma", "specialty": "Cardiology",
            "date_time": "2026-12-01T10:00:00", "location": "City Clinic"
        }
        res = client.post("/api/appointments/1", headers=_auth(STRANGER_TOKEN), json=body)
        assert res.status_code == 403

    def test_update_appointment_no_auth(self, client):
        res = client.put("/api/appointments/1", json={"notes": "Updated"})
        assert res.status_code == 401

    def test_update_appointment_expired_token(self, client):
        res = client.put("/api/appointments/1", headers=_auth(EXPIRED_TOKEN), json={"notes": "Updated"})
        assert res.status_code == 401

    def test_update_appointment_cross_profile_bola_forbidden(self, client):
        # Appointment 1 belongs to Profile 1. Stranger user cannot modify it.
        res = client.put("/api/appointments/1", headers=_auth(STRANGER_TOKEN), json={"notes": "Updated"})
        assert res.status_code == 403

    def test_delete_appointment_no_auth(self, client):
        res = client.delete("/api/appointments/1")
        assert res.status_code == 401

    def test_delete_appointment_cross_profile_bola_forbidden(self, client):
        res = client.delete("/api/appointments/1", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403


# ===========================================================================
# 5. FOLLOWUPS ROUTER  /api/followups
# ===========================================================================

class TestFollowupsAuth:

    def test_list_followups_no_auth(self, client):
        res = client.get("/api/followups/1")
        assert res.status_code == 401

    def test_list_followups_expired_token(self, client):
        res = client.get("/api/followups/1", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_list_followups_other_care_circle_forbidden(self, client):
        res = client.get("/api/followups/1", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_claim_followup_no_auth(self, client):
        body = {"dose_schedule_id": 2, "caregiver_id": 2, "action": "calling"}
        res = client.post("/api/followups/claim", json=body)
        assert res.status_code == 401

    def test_claim_followup_expired_token(self, client):
        body = {"dose_schedule_id": 2, "caregiver_id": 2, "action": "calling"}
        res = client.post("/api/followups/claim", headers=_auth(EXPIRED_TOKEN), json=body)
        assert res.status_code == 401

    def test_claim_followup_elderly_forbidden(self, client):
        # Only caregiver role can claim follow-up
        body = {"dose_schedule_id": 2, "caregiver_id": 1, "action": "calling"}
        res = client.post("/api/followups/claim", headers=_auth(ELDERLY_TOKEN), json=body)
        assert res.status_code == 403

    def test_claim_followup_family_forbidden(self, client):
        body = {"dose_schedule_id": 2, "caregiver_id": 3, "action": "calling"}
        res = client.post("/api/followups/claim", headers=_auth(FAMILY_TOKEN), json=body)
        assert res.status_code == 403

    def test_claim_followup_cross_profile_bola_forbidden(self, client):
        # Dose 2 belongs to Profile 1. Stranger user cannot claim it.
        body = {"dose_schedule_id": 2, "caregiver_id": 990, "action": "calling"}
        res = client.post("/api/followups/claim", headers=_auth(STRANGER_TOKEN), json=body)
        assert res.status_code == 403

    def test_claim_followup_caregiver_id_from_jwt(self, client):
        """Caregiver claims; body supplies forged caregiver_id=1. Server sets caregiver_id=2."""
        body = {"dose_schedule_id": 7, "caregiver_id": 1, "action": "calling"}
        res = client.post("/api/followups/claim", headers=_auth(CAREGIVER_TOKEN), json=body)
        assert res.status_code in (200, 201, 400, 409)
        if res.status_code in (200, 201):
            data = res.json()
            assert data.get("caregiver_id") == 2

    def test_update_followup_no_auth(self, client):
        res = client.put("/api/followups/1", json={"status": "resolved"})
        assert res.status_code == 401

    def test_update_followup_expired_token(self, client):
        res = client.put("/api/followups/1", headers=_auth(EXPIRED_TOKEN), json={"status": "resolved"})
        assert res.status_code == 401

    def test_update_followup_cross_profile_bola_forbidden(self, client):
        # Followup 1 belongs to Profile 1. Stranger user cannot update it.
        res = client.put("/api/followups/1", headers=_auth(STRANGER_TOKEN), json={"status": "resolved"})
        assert res.status_code == 403

    def test_update_followup_non_assigned_caregiver_forbidden(self, client):
        # Followup 1 is assigned to caregiver_id=2. Elderly (user 1) cannot update it.
        res = client.put("/api/followups/1", headers=_auth(ELDERLY_TOKEN), json={"status": "resolved"})
        assert res.status_code == 403


# ===========================================================================
# 6. CHANGES ROUTER  /api/changes
# ===========================================================================

class TestChangesAuth:

    def test_list_changes_no_auth(self, client):
        res = client.get("/api/changes/1")
        assert res.status_code == 401

    def test_list_changes_expired_token(self, client):
        res = client.get("/api/changes/1", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_list_changes_other_care_circle_forbidden(self, client):
        res = client.get("/api/changes/1", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_request_change_no_auth(self, client):
        body = {
            "medication_id": 1, "change_type": "dosage",
            "reason": "Test reason", "requested_by_user_id": 2
        }
        res = client.post("/api/changes/1", json=body)
        assert res.status_code == 401

    def test_request_change_expired_token(self, client):
        body = {
            "medication_id": 1, "change_type": "dosage",
            "reason": "Test reason", "requested_by_user_id": 2
        }
        res = client.post("/api/changes/1", headers=_auth(EXPIRED_TOKEN), json=body)
        assert res.status_code == 401

    def test_request_change_other_care_circle_forbidden(self, client):
        body = {
            "medication_id": 1, "change_type": "dosage",
            "reason": "Test reason", "requested_by_user_id": 990
        }
        res = client.post("/api/changes/1", headers=_auth(STRANGER_TOKEN), json=body)
        assert res.status_code == 403

    def test_request_change_identity_field_from_jwt(self, client):
        """Body has requested_by_user_id=1, but auth is caregiver (user_id=2).
        Server ignores body and derives requested_by_user_id from JWT (2).
        """
        body = {
            "medication_id": 1,
            "change_type": "dosage",
            "reason": "Side effect noted",
            "requested_by_user_id": 1
        }
        res = client.post("/api/changes/1", headers=_auth(CAREGIVER_TOKEN), json=body)
        assert res.status_code in (200, 201, 400, 409)
        if res.status_code in (200, 201):
            data = res.json()
            assert data.get("requested_by_user_id") == 2

    def test_review_change_no_auth(self, client):
        res = client.put("/api/changes/1/review", json={"status": "approved"})
        assert res.status_code == 401

    def test_review_change_expired_token(self, client):
        res = client.put("/api/changes/1/review", headers=_auth(EXPIRED_TOKEN), json={"status": "approved"})
        assert res.status_code == 401

    def test_review_change_cross_profile_bola_forbidden(self, client):
        # Change 1 belongs to Profile 1. Stranger user cannot review it.
        res = client.put("/api/changes/1/review", headers=_auth(STRANGER_TOKEN), json={"status": "approved"})
        assert res.status_code == 403

    def test_review_change_caregiver_forbidden(self, client):
        # Elderly sovereignty: only elderly patient can review medication changes
        res = client.put("/api/changes/1/review", headers=_auth(CAREGIVER_TOKEN), json={"status": "approved"})
        assert res.status_code == 403

    def test_review_change_family_forbidden(self, client):
        res = client.put("/api/changes/1/review", headers=_auth(FAMILY_TOKEN), json={"status": "approved"})
        assert res.status_code == 403

    def test_review_change_reviewed_by_from_jwt(self, client):
        """Body has reviewed_by_user_id=3 (family), but auth is elderly (user_id=1).
        Server derives reviewed_by_user_id from JWT (1).
        """
        body = {"status": "approved", "reviewed_by_user_id": 3}
        res = client.put("/api/changes/1/review", headers=_auth(ELDERLY_TOKEN), json=body)
        assert res.status_code in (200, 400, 409)
        if res.status_code == 200:
            data = res.json()
            assert data.get("reviewed_by_user_id") == 1


# ===========================================================================
# 7. NOTIFICATIONS ROUTER  /api/notifications
# ===========================================================================

class TestNotificationsAuth:

    def test_list_notifications_no_auth(self, client):
        res = client.get("/api/notifications/1")
        assert res.status_code == 401

    def test_list_notifications_expired_token(self, client):
        res = client.get("/api/notifications/1", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_list_notifications_other_care_circle_forbidden(self, client):
        res = client.get("/api/notifications/1", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_mark_read_no_auth(self, client):
        res = client.put("/api/notifications/1/read")
        assert res.status_code == 401

    def test_mark_read_expired_token(self, client):
        res = client.put("/api/notifications/1/read", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_mark_read_cross_profile_bola_forbidden(self, client):
        # Notification 1 belongs to Profile 1. Stranger user cannot mark it read.
        res = client.put("/api/notifications/1/read", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_mark_all_read_no_auth(self, client):
        res = client.put("/api/notifications/1/read-all")
        assert res.status_code == 401

    def test_mark_all_read_expired_token(self, client):
        res = client.put("/api/notifications/1/read-all", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_mark_all_read_other_care_circle_forbidden(self, client):
        res = client.put("/api/notifications/1/read-all", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403


# ===========================================================================
# 8. AI ROUTER  /api/ai
# ===========================================================================

class TestAiAuth:

    def test_scan_prescription_no_auth(self, client):
        res = client.post("/api/ai/scan-prescription")
        assert res.status_code == 401

    def test_scan_prescription_expired_token(self, client):
        res = client.post("/api/ai/scan-prescription", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_scan_prescription_invalid_token(self, client):
        res = client.post("/api/ai/scan-prescription", headers=_auth(INVALID_TOKEN))
        assert res.status_code == 401

    def test_weekly_summary_no_auth(self, client):
        res = client.post("/api/ai/weekly-summary/1")
        assert res.status_code == 401

    def test_weekly_summary_expired_token(self, client):
        res = client.post("/api/ai/weekly-summary/1", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_weekly_summary_other_care_circle_forbidden(self, client):
        # User 990 has no membership in Profile 1 -> 403
        res = client.post("/api/ai/weekly-summary/1", headers=_auth(STRANGER_TOKEN))
        assert res.status_code == 403

    def test_compare_prescription_no_auth(self, client):
        body = {"profile_id": 1, "extracted_items": [{"name": "Metformin", "dosage": "500mg"}]}
        res = client.post("/api/ai/compare-prescription", json=body)
        assert res.status_code == 401

    def test_compare_prescription_expired_token(self, client):
        body = {"profile_id": 1, "extracted_items": [{"name": "Metformin", "dosage": "500mg"}]}
        res = client.post("/api/ai/compare-prescription", headers=_auth(EXPIRED_TOKEN), json=body)
        assert res.status_code == 401

    def test_compare_prescription_other_care_circle_forbidden(self, client):
        body = {"profile_id": 1, "extracted_items": [{"name": "Metformin", "dosage": "500mg"}]}
        res = client.post("/api/ai/compare-prescription", headers=_auth(STRANGER_TOKEN), json=body)
        assert res.status_code == 403


# ===========================================================================
# 9. AUTH ROUTER & USER BOUNDARY
# ===========================================================================

class TestAuthRouterEdgeCases:

    def test_me_no_auth(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_me_expired_token(self, client):
        res = client.get("/api/auth/me", headers=_auth(EXPIRED_TOKEN))
        assert res.status_code == 401

    def test_me_invalid_token(self, client):
        res = client.get("/api/auth/me", headers=_auth(INVALID_TOKEN))
        assert res.status_code == 401

    def test_me_valid_user(self, client):
        res = client.get("/api/auth/me", headers=_auth(ELDERLY_TOKEN))
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["id"] == 1

    def test_nonexistent_user_token_rejected(self, client):
        res = client.get("/api/patients/1", headers=_auth(NONEXISTENT_USER_TOKEN))
        assert res.status_code == 401

    def test_demo_login_disabled_when_not_in_demo_mode(self, client):
        """When DEMO_MODE is false (default/production), /api/auth/demo-login returns 404."""
        import routers.auth as auth_module
        original = auth_module.DEMO_MODE
        try:
            auth_module.DEMO_MODE = False
            res = client.post("/api/auth/demo-login", json={"role": "elderly"})
            assert res.status_code == 404
        finally:
            auth_module.DEMO_MODE = original

    def test_demo_login_cannot_access_unrelated_profiles(self, client):
        """When DEMO_MODE is true, demo login works but cannot access profiles where
        the demo user has no membership.
        """
        import routers.auth as auth_module
        original = auth_module.DEMO_MODE
        try:
            auth_module.DEMO_MODE = True
            res = client.post("/api/auth/demo-login", json={"role": "elderly"})
            assert res.status_code == 200
            token = res.json().get("access_token")
            assert token

            # Profile 990 was created without user 1 as a member -> 403
            res2 = client.get("/api/patients/990", headers={"Authorization": f"Bearer {token}"})
            assert res2.status_code == 403
        finally:
            auth_module.DEMO_MODE = original
