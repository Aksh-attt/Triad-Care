export type UserRole = 'elderly' | 'caregiver' | 'family';

export interface User {
  id: number;
  name: string;
  email?: string;
  role: UserRole;
  passcode?: string;
}

export interface PatientProfile {
  id: number;
  name: string;
  age: number;
  medical_conditions: string[];
  allergies: string[];
  primary_doctor: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  notes?: string;
}

export interface ProfileMembership {
  id: number;
  profile_id: number;
  user_id: number;
  role: UserRole;
  user: User;
}

export interface Medication {
  id: number;
  profile_id: number;
  name: string;
  dosage: string;
  unit: string;
  frequency: string;
  timing_slots: string[];
  start_date: string;
  end_date?: string;
  instructions?: string;
  is_active: boolean;
  created_at: string;
}

export type DoseStatus = 'pending' | 'taken' | 'missed' | 'not_confirmed';

export interface DoseSchedule {
  id: number;
  medication_id: number;
  medication?: Medication;
  medication_name?: string;
  medication_dosage?: string;
  medication_unit?: string;
  scheduled_time: string;
  status: DoseStatus;
  confirmed_by_user_id?: number;
  confirmed_by_name?: string;
  confirmed_at?: string;
  reason_not_taken?: string;
  reason_notes?: string;
  followup?: CaregiverFollowup;
}

export interface Appointment {
  id: number;
  profile_id: number;
  doctor_name: string;
  specialty?: string;
  date_time: string;
  location?: string;
  notes?: string;
  reminder_sent: boolean;
}

export interface Notification {
  id: number;
  profile_id: number;
  user_id?: number;
  title: string;
  body: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export type FollowupAction = 'calling' | 'going_to_check' | 'unavailable';
export type FollowupStatus = 'unassigned' | 'accepted' | 'in_progress' | 'resolved' | 'reassigned';

export interface CaregiverFollowup {
  id: number;
  dose_schedule_id: number;
  caregiver_id: number;
  caregiver_name?: string;
  action: FollowupAction;
  status: FollowupStatus;
  accepted_at: string;
  resolved_at?: string;
  notes?: string;
  dose?: DoseSchedule;
}

export interface MedicationChangeRequest {
  id: number;
  profile_id: number;
  requested_by_user_id: number;
  requested_by_name?: string;
  medication_id?: number;
  medication_name?: string;
  change_type: string;
  proposed_details: Record<string, unknown>;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

export interface AuthState {
  user: User | null;
  profileId: number | null;
  profile: PatientProfile | null;
  isAuthenticated: boolean;
}
