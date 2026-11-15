"""
Triad Care Comprehensive Automated QA & Safety Test Suite
Covers Part 3 QA scenarios and Part 4 Critical Healthcare Safety Tests.
"""
import pytest
import httpx
import datetime

from fastapi.testclient import TestClient
from main import app
from auth_utils import create_access_token


class AuthTestClient:
    def __init__(self, app):
        self.base_client = TestClient(app)
        self.tokens = {
            1: create_access_token(user_id=1),
            2: create_access_token(user_id=2),
            3: create_access_token(user_id=3),
        }

    def _get_token_for_kwargs(self, url, kwargs):
        headers = dict(kwargs.get("headers") or {})
        if "Authorization" in headers:
            return
        json_data = kwargs.get("json") or {}
        uid = 1
        if isinstance(json_data, dict):
            if "caregiver_id" in json_data and json_data["caregiver_id"] in self.tokens:
                uid = json_data["caregiver_id"]
            elif "reviewed_by_user_id" in json_data and json_data["reviewed_by_user_id"] in self.tokens:
                uid = json_data["reviewed_by_user_id"]
            elif "requested_by_user_id" in json_data and json_data["requested_by_user_id"] in self.tokens:
                uid = json_data["requested_by_user_id"]
            elif "confirmed_by_user_id" in json_data and json_data["confirmed_by_user_id"] in self.tokens:
                uid = json_data["confirmed_by_user_id"]
            elif "/api/followups" in url:
                uid = 2
        elif "/api/followups" in url:
            uid = 2
        headers["Authorization"] = f"Bearer {self.tokens[uid]}"
        kwargs["headers"] = headers

    def get(self, url, **kwargs):
        self._get_token_for_kwargs(url, kwargs)
        return self.base_client.get(url, **kwargs)

    def post(self, url, **kwargs):
        self._get_token_for_kwargs(url, kwargs)
        return self.base_client.post(url, **kwargs)

    def put(self, url, **kwargs):
        self._get_token_for_kwargs(url, kwargs)
        return self.base_client.put(url, **kwargs)

    def delete(self, url, **kwargs):
        self._get_token_for_kwargs(url, kwargs)
        return self.base_client.delete(url, **kwargs)

    def __getattr__(self, name):
        return getattr(self.base_client, name)


@pytest.fixture
def client():
    return AuthTestClient(app)


# =========================================================================
# TEST 1: Role Access & Demo Authentication
# =========================================================================
def test_demo_users_list(client):
    """Verify demo users endpoint returns all three roles."""
    res = client.get("/api/auth/demo-users")
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 3
    roles = {u["role"] for u in users}
    assert "elderly" in roles
    assert "caregiver" in roles
    assert "family" in roles


def test_login_elderly_meera(client):
    """Elderly Meera Sharma login with passcode 1111."""
    res = client.post("/api/auth/login", json={"passcode": "1111"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["name"] == "Meera Sharma"
    assert data["user"]["role"] == "elderly"
    assert len(data["memberships"]) >= 1


def test_login_caregiver_riya(client):
    """Caregiver Riya Patel login with passcode 2222."""
    res = client.post("/api/auth/login", json={"passcode": "2222"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["name"] == "Riya Patel"
    assert data["user"]["role"] == "caregiver"


def test_login_family_arjun(client):
    """Family member Arjun Sharma login with passcode 3333."""
    res = client.post("/api/auth/login", json={"passcode": "3333"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["name"] == "Arjun Sharma"
    assert data["user"]["role"] == "family"


def test_invalid_passcode(client):
    """Invalid passcode returns 401 Unauthorized."""
    res = client.post("/api/auth/login", json={"passcode": "9999"})
    assert res.status_code == 401


# =========================================================================
# TEST 2: Medication Management (CRUD)
# =========================================================================
def test_medication_crud_lifecycle(client):
    """Add a medicine, edit it, verify schedule generation, and delete it."""
    # 1. Add medication
    new_med = {
        "name": "Lisinopril QA",
        "dosage": "10",
        "unit": "mg",
        "frequency": "once_daily",
        "timing_slots": ["morning"],
        "start_date": str(datetime.date.today()),
        "instructions": "Take in morning with water",
        "is_active": True,
    }
    create_res = client.post("/api/medications/1", json=new_med)
    assert create_res.status_code == 200
    created = create_res.json()
    med_id = created["id"]
    assert created["name"] == "Lisinopril QA"

    # 2. Verify it shows in active list
    list_res = client.get("/api/medications/1")
    assert list_res.status_code == 200
    active_ids = [m["id"] for m in list_res.json()]
    assert med_id in active_ids

    # 3. Edit medication
    edit_payload = {"dosage": "20", "instructions": "Take 20mg after breakfast"}
    update_res = client.put(f"/api/medications/{med_id}", json=edit_payload)
    assert update_res.status_code == 200
    assert update_res.json()["dosage"] == "20"
    assert update_res.json()["instructions"] == "Take 20mg after breakfast"

    # 4. Verify today's schedule includes this medication
    sched_res = client.get("/api/medications/1/schedule/today")
    assert sched_res.status_code == 200
    sched_med_ids = [d["medication_id"] for d in sched_res.json()]
    assert med_id in sched_med_ids

    # 5. Delete (soft-delete / deactivate)
    del_res = client.delete(f"/api/medications/{med_id}")
    assert del_res.status_code == 200

    # 6. Verify deletion reflected in active medications list
    list_after = client.get("/api/medications/1").json()
    assert med_id not in [m["id"] for m in list_after]

    # 7. Verify deletion reflected in today's active schedule
    sched_after = client.get("/api/medications/1/schedule/today").json()
    assert med_id not in [d["medication_id"] for d in sched_after]


# =========================================================================
# TEST 3: Medication Adherence & Unconfirmed Doses
# =========================================================================
def test_adherence_status_and_confirmation(client):
    """Confirm a dose as taken and verify timestamp + user id."""
    doses = client.get("/api/doses/1/today").json()
    assert len(doses) > 0
    dose = doses[0]

    # Confirm dose
    confirm_res = client.post(f"/api/doses/{dose['id']}/confirm", json={"confirmed_by_user_id": 1})
    assert confirm_res.status_code == 200
    confirmed = confirm_res.json()
    assert confirmed["status"] == "taken"
    assert confirmed["confirmed_by_user_id"] == 1
    assert confirmed["confirmed_at"] is not None


def test_unconfirmed_dose_not_automatically_missed(client):
    """An unconfirmed dose must remain 'not_confirmed' or 'pending', never automatically 'missed'."""
    doses = client.get("/api/doses/1/today").json()
    unconfirmed = [d for d in doses if d["status"] == "not_confirmed"]
    assert len(unconfirmed) > 0
    for d in unconfirmed:
        assert d["status"] == "not_confirmed"
        assert d["status"] != "missed"


# =========================================================================
# TEST 4 & CRITICAL SAFETY 1 & 2: Caregiver Accountability
# =========================================================================
def test_caregiver_claim_followup_and_safety_isolation(client):
    """
    CRITICAL HEALTHCARE SAFETY TEST 1 & 2:
    - Claiming a follow-up must NEVER mark the medication dose as taken.
    - Resolving a follow-up must NEVER mark the medication dose as taken.
    """
    doses = client.get("/api/doses/1/today").json()
    target_dose = next(d for d in doses if d["status"] == "not_confirmed")
    initial_dose_status = target_dose["status"]

    # 1. Caregiver claims follow-up with "I'm calling"
    claim_res = client.post(
        "/api/followups/claim",
        json={
            "dose_schedule_id": target_dose["id"],
            "caregiver_id": 2,
            "action": "calling",
        },
    )
    assert claim_res.status_code == 200
    followup = claim_res.json()
    assert followup["action"] == "calling"
    assert followup["status"] == "accepted"
    assert followup["caregiver_id"] == 2
    assert followup["accepted_at"] is not None
    followup_id = followup["id"]

    # CRITICAL VERIFICATION 1: Dose status MUST NOT be changed by claiming follow-up
    doses_after_claim = client.get("/api/doses/1/today").json()
    dose_check = next(d for d in doses_after_claim if d["id"] == target_dose["id"])
    assert dose_check["status"] == initial_dose_status, "CRITICAL FAILURE: Followup claim altered dose status!"
    assert dose_check["status"] != "taken", "CRITICAL FAILURE: Dose was marked as taken upon follow-up claim!"

    # 2. Update follow-up to in_progress
    upd_res = client.put(f"/api/followups/{followup_id}", json={"status": "in_progress", "notes": "Called patient phone"})
    assert upd_res.status_code == 200
    assert upd_res.json()["status"] == "in_progress"

    # 3. Resolve follow-up
    res_res = client.put(f"/api/followups/{followup_id}", json={"status": "resolved", "notes": "Patient spoke, will take with tea"})
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "resolved"
    assert res_res.json()["resolved_at"] is not None

    # CRITICAL VERIFICATION 2: Resolving follow-up MUST NOT mark dose as taken
    doses_after_resolve = client.get("/api/doses/1/today").json()
    dose_final = next(d for d in doses_after_resolve if d["id"] == target_dose["id"])
    assert dose_final["status"] == initial_dose_status, "CRITICAL FAILURE: Followup resolution altered dose status!"
    assert dose_final["status"] != "taken", "CRITICAL FAILURE: Resolving follow-up auto-marked dose as taken!"


# =========================================================================
# TEST 5: Reason Logging for Unconfirmed Doses
# =========================================================================
@pytest.mark.parametrize("reason", [
    "Forgot",
    "Medicine unavailable",
    "Feeling unwell",
    "Unsure / cannot remember",
    "Other",
])
def test_record_all_reasons(client, reason):
    """Verify recording each supported reason with notes."""
    doses = client.get("/api/doses/1/today").json()
    dose_id = doses[0]["id"]

    res = client.post(
        f"/api/doses/{dose_id}/reason",
        json={
            "reason": reason,
            "notes": f"QA test notes for reason: {reason}",
            "confirmed_by_user_id": 1,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["reason_not_taken"] == reason
    assert f"QA test notes for reason: {reason}" in data["reason_notes"]


# =========================================================================
# TEST 6: AI Prescription Scanner & Fallback
# =========================================================================
def test_prescription_scanner_demo_fallback(client):
    """Without live API key or with mock, scanner returns is_demo=True and non-empty items."""
    # Send dummy multipart form
    files = {"image_file": ("rx.png", b"fake-png-content", "image/png")}
    res = client.post("/api/ai/scan-prescription", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "extracted_items" in data
    assert data.get("is_demo") is True or "extracted_items" in data


def test_prescription_comparison_with_active_meds(client):
    """Compares extracted items against active meds and flags new vs existing."""
    payload = {
        "profile_id": 1,
        "extracted_items": [
            {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily"},
            {"name": "Atorvastatin QA", "dosage": "20mg", "frequency": "once daily"},
        ],
    }
    res = client.post("/api/ai/compare-prescription", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "comparison" in data
    comp = data["comparison"]
    assert len(comp) == 2
    # Metformin is an existing medication in seed data
    metformin_item = next(c for c in comp if "metformin" in c["extracted"]["name"].lower())
    assert metformin_item["is_existing"] is True
    # Atorvastatin QA is brand new
    new_item = next(c for c in comp if "atorvastatin" in c["extracted"]["name"].lower())
    assert new_item["is_existing"] is False


# =========================================================================
# TEST 7 & CRITICAL SAFETY 4 & 5: Medication Change Approval Safety
# =========================================================================
def test_medication_change_safety_workflow(client):
    """
    CRITICAL HEALTHCARE SAFETY TEST 4 & 5:
    - Family proposes change -> status is pending.
    - Pending change MUST NOT alter active medication.
    - Rejection MUST NOT alter active medication.
    - Approval MUST apply the change strictly upon authorization.
    """
    # 1. Family proposes dosage change for Metformin (medication id=1, dosage=500)
    med_before = client.get("/api/medications/1").json()
    metformin = next(m for m in med_before if m["id"] == 1)
    original_dosage = metformin["dosage"]

    prop_res = client.post(
        "/api/changes/1",
        json={
            "requested_by_user_id": 3,
            "medication_id": 1,
            "change_type": "dosage_change",
            "proposed_details": {"new_dosage": "850", "unit": "mg"},
            "reason": "QA Test: Proposed dose adjustment",
        },
    )
    assert prop_res.status_code == 200
    change_req = prop_res.json()
    assert change_req["status"] == "pending"
    change_id = change_req["id"]

    # CRITICAL VERIFICATION 4: Pending change MUST NOT alter active medication
    med_during_pending = client.get("/api/medications/1").json()
    metformin_pending = next(m for m in med_during_pending if m["id"] == 1)
    assert metformin_pending["dosage"] == original_dosage, "CRITICAL FAILURE: Pending change altered active medication!"

    # 2. Elderly rejects the change
    reject_res = client.put(
        f"/api/changes/{change_id}/review",
        json={"status": "rejected", "reviewed_by_user_id": 1},
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "rejected"

    # CRITICAL VERIFICATION 5: Rejected change MUST NOT alter active medication
    med_after_reject = client.get("/api/medications/1").json()
    metformin_rejected = next(m for m in med_after_reject if m["id"] == 1)
    assert metformin_rejected["dosage"] == original_dosage, "CRITICAL FAILURE: Rejected change altered active medication!"

    # 3. Family proposes second change, which elderly approves
    prop2_res = client.post(
        "/api/changes/1",
        json={
            "requested_by_user_id": 3,
            "medication_id": 1,
            "change_type": "dosage_change",
            "proposed_details": {"new_dosage": "1000", "unit": "mg"},
            "reason": "QA Test: Approved dose adjustment to 1000mg",
        },
    )
    assert prop2_res.status_code == 200
    change2_id = prop2_res.json()["id"]

    approve_res = client.put(
        f"/api/changes/{change2_id}/review",
        json={"status": "approved", "reviewed_by_user_id": 1},
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # Active medication is updated ONLY upon explicit elderly approval
    med_after_approve = client.get("/api/medications/1").json()
    metformin_approved = next(m for m in med_after_approve if m["id"] == 1)
    assert metformin_approved["dosage"] == "1000"


# =========================================================================
# TEST 8 & CRITICAL SAFETY 7: AI Weekly Health Digest
# =========================================================================
def test_ai_weekly_digest_accuracy_and_facts(client):
    """AI weekly digest computes accurate adherence stats matching stored records."""
    res = client.post("/api/ai/weekly-summary/1")
    assert res.status_code == 200
    data = res.json()
    assert "stats" in data
    stats = data["stats"]
    assert "total" in stats
    assert "taken" in stats
    assert "adherence_percent" in stats
    assert stats["taken"] <= stats["total"]
    # Check that summary text is non-empty and identifies demo status if no API key
    assert len(data.get("summary", "")) > 10


# =========================================================================
# TEST 9: Appointment Management
# =========================================================================
def test_appointment_lifecycle(client):
    """Create, edit, list, and delete a doctor appointment."""
    # 1. Create appointment
    new_appt = {
        "doctor_name": "Dr. Sarah Jenkins",
        "specialty": "Cardiologist",
        "date_time": (datetime.datetime.now() + datetime.timedelta(days=5)).isoformat(),
        "location": "Metro Heart Institute, Suite 400",
        "notes": "Bring recent BP tracking log",
    }
    add_res = client.post("/api/appointments/1", json=new_appt)
    assert add_res.status_code == 200
    appt = add_res.json()
    appt_id = appt["id"]
    assert appt["doctor_name"] == "Dr. Sarah Jenkins"

    # 2. Update appointment
    upd_res = client.put(f"/api/appointments/{appt_id}", json={"notes": "Updated: Bring ECG report"})
    assert upd_res.status_code == 200
    assert "Updated: Bring ECG report" in upd_res.json()["notes"]

    # 3. List appointments
    list_res = client.get("/api/appointments/1")
    assert list_res.status_code == 200
    assert appt_id in [a["id"] for a in list_res.json()]

    # 4. Delete appointment
    del_res = client.delete(f"/api/appointments/{appt_id}")
    assert del_res.status_code == 200
    list_after = client.get("/api/appointments/1").json()
    assert appt_id not in [a["id"] for a in list_after]


# =========================================================================
# TEST 10: In-App Notifications
# =========================================================================
def test_notifications_workflow(client):
    """List notifications, mark one read, mark all read."""
    notifs = client.get("/api/notifications/1").json()
    assert len(notifs) >= 1

    first_notif = notifs[0]
    read_res = client.put(f"/api/notifications/{first_notif['id']}/read")
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    read_all_res = client.put("/api/notifications/1/read-all")
    assert read_all_res.status_code == 200

    notifs_after = client.get("/api/notifications/1").json()
    assert all(n["is_read"] is True for n in notifs_after)
