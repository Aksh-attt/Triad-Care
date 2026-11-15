import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import (
    User, PatientProfile, ProfileMembership, Medication,
    DoseSchedule, Appointment, Notification, CaregiverFollowup,
    MedicationChangeRequest
)
from auth_utils import hash_password


async def seed_database(db: AsyncSession):
    # Check if already seeded
    result = await db.execute(select(User))
    existing = result.scalars().first()
    if existing:
        return

    today = datetime.date.today()
    now = datetime.datetime.now()

    # Users – hashed_password used instead of plaintext passcode
    users = [
        User(id=1, name="Meera Sharma", role="elderly",
             hashed_password=hash_password("1111"), is_demo=True, is_active=True),
        User(id=2, name="Riya Patel", role="caregiver",
             hashed_password=hash_password("2222"), is_demo=True, is_active=True),
        User(id=3, name="Arjun Sharma", role="family",
             hashed_password=hash_password("3333"), is_demo=True, is_active=True),
    ]
    db.add_all(users)
    await db.flush()

    # Patient Profile – explicitly marked as is_demo=True for demo isolation
    profile = PatientProfile(
        id=1,
        name="Meera Sharma",
        age=72,
        is_demo=True,
        medical_conditions=["Type 2 Diabetes", "Hypertension", "Mild Arthritis"],
        allergies=["Penicillin"],
        primary_doctor="Dr. Priya Nair",
        emergency_contact_name="Arjun Sharma",
        emergency_contact_phone="+91-9876543210",
    )
    db.add(profile)
    await db.flush()

    # Memberships
    memberships = [
        ProfileMembership(profile_id=1, user_id=1, role="elderly", status="active", permissions={}),
        ProfileMembership(profile_id=1, user_id=2, role="caregiver", status="active", permissions={}),
        ProfileMembership(profile_id=1, user_id=3, role="family", status="active", permissions={}),
    ]
    db.add_all(memberships)
    await db.flush()

    # Medications
    meds = [
        Medication(
            id=1, profile_id=1, name="Metformin", dosage="500", unit="mg",
            frequency="twice_daily", timing_slots=["morning", "evening"],
            start_date=today - datetime.timedelta(days=30), is_active=True
        ),
        Medication(
            id=2, profile_id=1, name="Amlodipine", dosage="5", unit="mg",
            frequency="once_daily", timing_slots=["morning"],
            start_date=today - datetime.timedelta(days=60), is_active=True
        ),
        Medication(
            id=3, profile_id=1, name="Aspirin", dosage="75", unit="mg",
            frequency="once_daily", timing_slots=["morning"],
            start_date=today - datetime.timedelta(days=90), is_active=True
        ),
        Medication(
            id=4, profile_id=1, name="Calcium+Vit D3", dosage="500", unit="mg",
            frequency="once_daily", timing_slots=["evening"],
            start_date=today - datetime.timedelta(days=45), is_active=True
        ),
        Medication(
            id=5, profile_id=1, name="Pantoprazole", dosage="40", unit="mg",
            frequency="once_daily", timing_slots=["morning"],
            start_date=today - datetime.timedelta(days=20),
            instructions="Before food", is_active=True
        ),
    ]
    db.add_all(meds)
    await db.flush()

    # Today's dose schedules
    metformin_morning_time = datetime.datetime.combine(today, datetime.time(8, 0))
    metformin_morning_confirmed_at = datetime.datetime.combine(today, datetime.time(8, 30))
    amlodipine_morning_time = datetime.datetime.combine(today, datetime.time(9, 0))
    aspirin_morning_time = datetime.datetime.combine(today, datetime.time(9, 0))
    pantoprazole_morning_time = datetime.datetime.combine(today, datetime.time(7, 30))
    pantoprazole_confirmed_at = datetime.datetime.combine(today, datetime.time(7, 45))
    metformin_evening_time = datetime.datetime.combine(today, datetime.time(20, 0))
    calcium_evening_time = datetime.datetime.combine(today, datetime.time(19, 0))

    doses = [
        DoseSchedule(
            id=1, medication_id=1, scheduled_time=metformin_morning_time,
            status="taken", confirmed_by_user_id=2,
            confirmed_at=metformin_morning_confirmed_at
        ),
        DoseSchedule(
            id=2, medication_id=2, scheduled_time=amlodipine_morning_time,
            status="not_confirmed"
        ),
        DoseSchedule(
            id=3, medication_id=3, scheduled_time=aspirin_morning_time,
            status="not_confirmed"
        ),
        DoseSchedule(
            id=4, medication_id=5, scheduled_time=pantoprazole_morning_time,
            status="taken", confirmed_by_user_id=1,
            confirmed_at=pantoprazole_confirmed_at
        ),
        DoseSchedule(
            id=5, medication_id=1, scheduled_time=metformin_evening_time,
            status="pending"
        ),
        DoseSchedule(
            id=6, medication_id=4, scheduled_time=calcium_evening_time,
            status="pending"
        ),
    ]
    db.add_all(doses)
    await db.flush()

    # CaregiverFollowup for Amlodipine morning dose (dose id=2)
    followup = CaregiverFollowup(
        dose_schedule_id=2,
        caregiver_id=2,
        action="going_to_check",
        status="in_progress",
        accepted_at=now - datetime.timedelta(minutes=30),
    )
    db.add(followup)
    await db.flush()

    # Appointment
    appt_date = datetime.datetime.combine(
        today + datetime.timedelta(days=3), datetime.time(10, 30)
    )
    appointment = Appointment(
        profile_id=1,
        doctor_name="Dr. Priya Nair",
        specialty="General Physician",
        date_time=appt_date,
        location="City Health Clinic",
    )
    db.add(appointment)
    await db.flush()

    # Notifications
    notifications = [
        Notification(
            profile_id=1,
            title="Amlodipine dose overdue",
            body="Amlodipine dose overdue - Riya is handling follow-up",
            type="medication_missed",
            is_read=False,
        ),
        Notification(
            profile_id=1,
            title="Upcoming appointment",
            body="Upcoming appointment with Dr. Priya Nair in 3 days",
            type="appointment_reminder",
            is_read=True,
        ),
        Notification(
            profile_id=1,
            user_id=3,
            title="Medication change request",
            body="Arjun has requested a medication change for Aspirin",
            type="change_request",
            is_read=False,
        ),
    ]
    db.add_all(notifications)
    await db.flush()

    # MedicationChangeRequest
    change_req = MedicationChangeRequest(
        profile_id=1,
        requested_by_user_id=3,
        medication_id=3,  # Aspirin
        change_type="dosage_change",
        proposed_details={"new_dosage": "100", "unit": "mg"},
        reason="New prescription from cardiologist",
        status="pending",
    )
    db.add(change_req)
    await db.commit()
    print("✅ Demo data seeded successfully.")
