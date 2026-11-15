from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, JSON, func
)
from sqlalchemy.orm import relationship
from database import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    role = Column(String, nullable=False)  # elderly/caregiver/family
    passcode = Column(String(4), nullable=False)
    created_at = Column(DateTime, default=func.now())

    memberships = relationship("ProfileMembership", back_populates="user")
    confirmed_doses = relationship("DoseSchedule", back_populates="confirmed_by_user", foreign_keys="DoseSchedule.confirmed_by_user_id")
    followups = relationship("CaregiverFollowup", back_populates="caregiver")
    notifications = relationship("Notification", back_populates="user")
    change_requests = relationship("MedicationChangeRequest", back_populates="requested_by_user", foreign_keys="MedicationChangeRequest.requested_by_user_id")


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    medical_conditions = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    primary_doctor = Column(String, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    memberships = relationship("ProfileMembership", back_populates="profile")
    medications = relationship("Medication", back_populates="profile")
    appointments = relationship("Appointment", back_populates="profile")
    notifications = relationship("Notification", back_populates="profile")
    prescriptions = relationship("Prescription", back_populates="profile")
    change_requests = relationship("MedicationChangeRequest", back_populates="profile")


class ProfileMembership(Base):
    __tablename__ = "profile_memberships"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)
    joined_at = Column(DateTime, default=func.now())

    profile = relationship("PatientProfile", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    frequency = Column(String, nullable=False)  # once_daily/twice_daily/thrice_daily/as_needed
    timing_slots = Column(JSON, default=list)  # ["morning","evening"]
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    instructions = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    added_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    profile = relationship("PatientProfile", back_populates="medications")
    added_by_user = relationship("User", foreign_keys=[added_by_user_id])
    dose_schedules = relationship("DoseSchedule", back_populates="medication")
    change_requests = relationship("MedicationChangeRequest", back_populates="medication")


class DoseSchedule(Base):
    __tablename__ = "dose_schedules"

    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # pending/taken/missed/not_confirmed
    confirmed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    reason_not_taken = Column(String, nullable=True)
    reason_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    medication = relationship("Medication", back_populates="dose_schedules")
    confirmed_by_user = relationship("User", back_populates="confirmed_doses", foreign_keys=[confirmed_by_user_id])
    followups = relationship("CaregiverFollowup", back_populates="dose_schedule")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    doctor_name = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    date_time = Column(DateTime, nullable=False)
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    profile = relationship("PatientProfile", back_populates="appointments")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    profile = relationship("PatientProfile", back_populates="notifications")
    user = relationship("User", back_populates="notifications")


class CaregiverFollowup(Base):
    __tablename__ = "caregiver_followups"

    id = Column(Integer, primary_key=True, index=True)
    dose_schedule_id = Column(Integer, ForeignKey("dose_schedules.id"), nullable=False)
    caregiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # calling/going_to_check/unavailable
    status = Column(String, default="accepted")  # unassigned/accepted/in_progress/resolved/reassigned
    accepted_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    dose_schedule = relationship("DoseSchedule", back_populates="followups")
    caregiver = relationship("User", back_populates="followups")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String, nullable=True)
    raw_ai_response = Column(Text, nullable=True)
    extracted_items = Column(JSON, default=list)
    status = Column(String, default="pending_review")  # pending_review/approved/rejected
    uploaded_at = Column(DateTime, default=func.now())

    profile = relationship("PatientProfile", back_populates="prescriptions")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by_user_id])


class MedicationChangeRequest(Base):
    __tablename__ = "medication_change_requests"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)
    change_type = Column(String, nullable=False)  # new_medicine/dosage_change/frequency_change/discontinue
    proposed_details = Column(JSON, default=dict)
    reason = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending/approved/rejected
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    profile = relationship("PatientProfile", back_populates="change_requests")
    requested_by_user = relationship("User", back_populates="change_requests", foreign_keys=[requested_by_user_id])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by_user_id])
    medication = relationship("Medication", back_populates="change_requests")
