from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime, date


# ---- User ----
class UserBase(BaseModel):
    name: str
    email: Optional[str] = None
    role: str
    passcode: str


class UserCreate(UserBase):
    pass


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: Optional[str] = None
    role: str
    created_at: Optional[datetime] = None


# ---- ProfileMembership ----
class MembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    user_id: int
    role: str
    joined_at: Optional[datetime] = None
    user: Optional[UserOut] = None


# ---- PatientProfile ----
class PatientProfileBase(BaseModel):
    name: str
    age: Optional[int] = None
    date_of_birth: Optional[date] = None
    medical_conditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    primary_doctor: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None


class PatientProfileCreate(PatientProfileBase):
    pass


class PatientProfileUpdate(PatientProfileBase):
    pass


class PatientProfileOut(PatientProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None


# ---- Medication ----
class MedicationBase(BaseModel):
    name: str
    dosage: str
    unit: str
    frequency: str
    timing_slots: Optional[List[str]] = []
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = True
    added_by_user_id: Optional[int] = None


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    unit: Optional[str] = None
    frequency: Optional[str] = None
    timing_slots: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = None


class MedicationOut(MedicationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---- DoseSchedule ----
class DoseScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    medication_id: int
    scheduled_time: datetime
    status: str
    confirmed_by_user_id: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    confirmation_method: Optional[str] = None
    reason_not_taken: Optional[str] = None
    reason_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    medication: Optional[MedicationOut] = None


class DoseConfirm(BaseModel):
    confirmed_by_user_id: Optional[int] = None
    confirmation_method: Optional[str] = "patient_confirmed"  # patient_confirmed|caregiver_observed|caregiver_reported


class DoseReason(BaseModel):
    reason: str
    notes: Optional[str] = None
    confirmed_by_user_id: Optional[int] = None


# ---- Appointment ----
class AppointmentBase(BaseModel):
    doctor_name: str
    specialty: Optional[str] = None
    date_time: datetime
    location: Optional[str] = None
    notes: Optional[str] = None
    reminder_sent: Optional[bool] = False


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    doctor_name: Optional[str] = None
    specialty: Optional[str] = None
    date_time: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    reminder_sent: Optional[bool] = None


class AppointmentOut(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---- Notification ----
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    user_id: Optional[int] = None
    title: str
    body: str
    type: str
    is_read: bool
    created_at: Optional[datetime] = None


# ---- CaregiverFollowup ----
class FollowupClaim(BaseModel):
    dose_schedule_id: int
    caregiver_id: Optional[int] = None
    action: str


class FollowupUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    action: Optional[str] = None
    resolved_at: Optional[datetime] = None


class FollowupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dose_schedule_id: int
    caregiver_id: int
    action: str
    status: str
    accepted_at: datetime
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    dose_schedule: Optional[DoseScheduleOut] = None
    caregiver: Optional[UserOut] = None


# ---- Prescription ----
class PrescriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    uploaded_by_user_id: Optional[int] = None
    image_path: Optional[str] = None
    raw_ai_response: Optional[str] = None
    extracted_items: Optional[List[Any]] = []
    status: str
    uploaded_at: Optional[datetime] = None


# ---- MedicationChangeRequest ----
class ChangeRequestBase(BaseModel):
    medication_id: Optional[int] = None
    change_type: str
    proposed_details: Optional[Any] = {}
    reason: str
    requested_by_user_id: Optional[int] = None


class ChangeRequestCreate(ChangeRequestBase):
    pass


class ChangeRequestUpdate(BaseModel):
    status: str
    reviewed_by_user_id: Optional[int] = None


class ChangeRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    requested_by_user_id: int
    medication_id: Optional[int] = None
    change_type: str
    proposed_details: Optional[Any] = {}
    reason: str
    status: str
    reviewed_by_user_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    requested_by_user: Optional[UserOut] = None
    medication: Optional[MedicationOut] = None


# ---- Auth ----
class LoginRequest(BaseModel):
    username: Optional[str] = None    # name or email
    password: Optional[str] = None    # plaintext (sent over HTTPS; never stored)
    passcode: Optional[str] = None    # demo passcode for legacy/demo compatibility


class LoginResponse(BaseModel):
    user: UserOut
    memberships: List[MembershipOut]
    access_token: Optional[str] = None   # None in /me response (no new token issued)
    csrf_token: Optional[str] = None     # None in /me response
