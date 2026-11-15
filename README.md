# Triad Care — AI-Powered Elderly Care Coordination & Accountability Platform

> **"Care that connects. Responsibility that follows."**

Triad Care is an AI-powered elderly care coordination and accountability platform connecting elderly individuals, caregivers, and family members through one unified, shared healthcare profile. Built for hackathon demonstration with production-ready architecture, high-accessibility UX, and clean separation between business logic and UI templates.

---

## 🌟 The Three Pillars

1. **Intelligence** — AI-assisted prescription OCR scanning, medication schedule diffing, and compassionate adherence summaries powered by Google Gemini.
2. **Accountability** — The flagship **"I'm handling it"** caregiver follow-up engine that ensures overdue doses are assigned, tracked, and resolved without confusing dose status with follow-up status.
3. **Independence** — Elderly patients remain in full control of their health data; medication changes proposed by family members require patient review and approval before becoming active.

---

## 🏗️ Technology Stack & Replaceable UI Architecture

Triad Care was intentionally designed following a **functionality-first, modular architecture** so that any external UI template (Tailwind UI, Shadcn, or custom theme) can be plugged in later without rebuilding backend APIs or rewiring state:

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts (analytics), Axios.
  - *Separation:* Business logic in `/src/api`, `/src/store`, and `/src/types` is completely decoupled from visual presentation in `/src/pages` and `/src/components/ui`.
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async with `aiosqlite`), Pydantic v2 schemas.
  - *Data layer:* SQLite by default for zero-friction local demos; connection string and models cleanly structured for direct migration to PostgreSQL / Supabase.
- **AI Engine:** Google Gemini API (`gemini-1.5-flash` / Gemini Vision) with built-in graceful demo fallback (`is_demo=true`) when API keys are not supplied.

---

## 👥 Demo Personas & Passcodes

For rapid testing and judging, Triad Care features **Instant One-Click Demo Logins** on the login screen as well as a live role switcher in the top navigation bar:

| Persona | Role | Passcode | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **Meera Sharma** (Age 72) | `elderly` | `1111` | High-contrast UI, one-touch **"✓ I've taken it"**, approve/reject medication change proposals, view appointments. |
| **Riya Patel** | `caregiver` | `2222` | Overdue dose triage, **"I'm handling it"** follow-up workflow (Calling, Going to check, Unavailable), follow-up resolution, patient medical profile. |
| **Arjun Sharma** (Son) | `family` | `3333` | Adherence analytics (Recharts), real-time caregiver accountability transparency, propose medication changes, manage doctor appointments. |

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Start the Backend
```bash
cd backend
# (Optional) create and activate venv
python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
The backend initializes the SQLite database (`caresync.db`) and seeds synthetic demo data automatically on startup.
- API Documentation (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
- Web Application: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 🎯 Features Implemented

### 1. Shared Healthcare Dashboard & Adherence Tracking
- Unified patient profile for Meera Sharma with chronic conditions (Type 2 Diabetes, Hypertension, Mild Arthritis), allergies (Penicillin), and primary doctor.
- Statuses for all scheduled doses: `taken`, `missed`, `not_confirmed`, and `pending`.
- **Safety guarantee:** Overdue doses are never automatically presumed missed without explicit logging.
- Doses record exact timestamps and the user who confirmed them.

### 2. Caregiver Accountability — *"I'm handling it"* (Differentiator)
- When a dose is unconfirmed or overdue, caregivers can claim direct responsibility with one of three predefined actions:
  - 📞 **I'm calling** (phone check-in)
  - 🏃 **I'm going to check** (in-person home visit)
  - ❌ **I'm unavailable** (flags for reassignment)
- Tracks state progression: `accepted` → `in_progress` → `resolved`.
- **Critical Business Rule:** Claiming or resolving a follow-up **NEVER** marks a dose as taken. Dose schedules and caregiver follow-ups are separate entities.
- Live visibility on the Family Dashboard shows exactly who is currently following up.

### 3. "Why wasn't it taken?" Reason Logging
- Elderly patients or caregivers can record why a dose was skipped or delayed:
  - *Forgot*
  - *Medicine unavailable / Refill needed*
  - *Feeling unwell*
  - *Unsure / cannot remember*
  - *Other (with notes)*
- Prevents misinterpreting unconfirmed doses and provides clinical context for doctors.

### 4. Medication Change Request & Approval Workflow
- Family members cannot unilaterally alter elderly medication schedules.
- Proposing a new medicine, dosage change, or discontinuation generates a `pending` request.
- The elderly patient must explicitly **Approve** or **Reject** the proposal from their dashboard before it becomes active in the database.

### 5. AI Prescription Scanner & Schedule Comparison
- Upload prescription photos or doctor notes.
- Gemini Vision OCR extracts medication name, dosage, unit, frequency, and instructions.
- Compares extracted medicines against active prescriptions, flagging existing vs. newly introduced drugs.
- Editable review screen ensures human verification before saving.
- Graceful demo fallback when `GEMINI_API_KEY` is not provided.

### 6. AI Healthcare Weekly Digest
- Aggregates adherence data, recorded missed dose reasons, caregiver follow-ups, and upcoming appointments.
- Synthesizes compassionate, plain-language insights for the family and patient.
- Clearly distinguishes raw clinical facts from AI-generated commentary.

### 7. Doctor Appointment Management
- Schedule, update, and manage doctor visits (doctor name, department/specialty, location, datetime, questions/notes).

### 8. In-App Notification Center
- Real-time alerts for overdue medications, caregiver follow-up assignments, appointment reminders, and change proposals.

---

## 🎬 Step-by-Step Demo Walkthrough for Judges

1. **Open App:** Navigate to [http://127.0.0.1:5173](http://127.0.0.1:5173).
2. **Step 1: Elderly Experience (Independence)**
   - Click **"Enter as Meera (1111)"**.
   - Note the high-contrast, welcoming greeting.
   - See the prominent **"Next Scheduled Medication"** card and click **"✓ I've taken it!"**.
   - Notice the **"Medication Change Request"** banner: Arjun has proposed increasing Aspirin to 100mg. Review and click **"Approve Change"**. Notice the schedule updates instantly.
3. **Step 2: Caregiver Experience (Accountability)**
   - Use the demo switcher in the top bar to switch to **"Riya"**.
   - On Riya's dashboard, notice the **Unconfirmed / Overdue Doses** section.
   - Click **"I'm handling it"** on an unconfirmed dose.
   - Select **"🏃 I'm going to check"** and click **"Confirm"**.
   - Notice the follow-up appears under **Active Caregiver Follow-ups** as `in_progress`.
   - Click **"Mark Follow-up Resolved"** once completed.
4. **Step 3: Family Monitoring Experience (Peace of Mind)**
   - Switch to **"Arjun"** in the top bar.
   - View the live **Adherence Overview** pie chart and statistics.
   - View the **Caregiver Follow-up Transparency** card showing Riya's logged follow-up.
   - Click **"+ Propose Med Change"** to propose a new medication or dose adjustment.
5. **Step 4: AI Intelligence**
   - Click **"AI Features"** in the sidebar.
   - In **Prescription Scanner**, upload a prescription image to test OCR extraction and schedule comparison.
   - Switch to **Weekly Adherence Summary** and click **"Generate Weekly Summary"** to view compassionate AI-driven health insights.

---

## 📂 Project Directory Structure

```
catalysthackathon/
├── backend/
│   ├── main.py              # FastAPI app with CORS & lifespan DB init
│   ├── database.py          # Async SQLAlchemy engine & session maker
│   ├── models.py            # ORM models (User, Medication, DoseSchedule, etc.)
│   ├── schemas.py           # Pydantic v2 serialization schemas
│   ├── seed.py              # Synthetic demo data generator
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Backend environment variables
│   └── routers/
│       ├── auth.py          # Demo users & passcode authentication
│       ├── patients.py      # Patient profiles and memberships
│       ├── medications.py   # Medication CRUD & daily schedule
│       ├── doses.py         # Dose confirmation & reason logging
│       ├── appointments.py  # Doctor appointment management
│       ├── followups.py     # "I'm handling it" caregiver accountability
│       ├── notifications.py # In-app alerts
│       ├── ai.py            # Gemini Vision OCR & adherence digest
│       └── changes.py       # Medication change proposals & elderly approval
├── frontend/
│   ├── package.json         # React 19, Vite, Tailwind CSS, Lucide, Recharts
│   ├── tailwind.config.js   # Tailored theme (navy, teal, success, warning)
│   ├── postcss.config.js    # PostCSS configuration
│   └── src/
│       ├── App.tsx          # Role-based protected routes
│       ├── main.tsx         # React root mounting
│       ├── types/index.ts   # TypeScript interfaces matching backend models
│       ├── store/authStore.tsx # Authentication context & demo switching
│       ├── api/             # Modular API clients (Axios)
│       ├── components/
│       │   ├── ui/          # Replaceable UI elements (Button, Card, Modal, etc.)
│       │   ├── layout/      # AppLayout, Sidebar, TopBar, NotificationBell
│       │   ├── medications/ # DoseCard, MedicationCard, MedicationForm, RecordReasonModal
│       │   ├── followups/   # ClaimFollowupModal, FollowupCard
│       │   ├── appointments/# AppointmentCard, AppointmentForm
│       │   ├── changes/     # ChangeRequestCard, ChangeRequestForm
│       │   └── ai/          # PrescriptionScanner, WeeklySummary
│       └── pages/
│           ├── LoginPage.tsx
│           ├── elderly/     # ElderlyDashboard, ElderlyMedications, ElderlyAppointments
│           ├── caregiver/   # CaregiverDashboard, CaregiverFollowups, CaregiverPatients
│           ├── family/      # FamilyDashboard, FamilyMedications, FamilyAppointments, FamilyChanges
│           └── shared/      # AIFeatures, NotificationsPage
├── .env.example             # Project-wide environment template
└── README.md                # Comprehensive documentation
```

---

## 🛡️ Future UI Template Replacement (Section 13 Compliance)

The visual layer is strictly separated from data and business logic:
1. **API & Data layer (`/src/api`, `/src/types`)**: Pure TypeScript contracts independent of any styling.
2. **State & Auth (`/src/store`)**: Role-based state management that works with any UI framework.
3. **Core Functional Components (`/src/components/*`)**: Cleanly organized into functional domains (Medications, Followups, Changes, Appointments, AI).
4. When applying a new UI kit (e.g. Tailwind UI, Shadcn, or custom CSS), replace the presentation wrappers in `/src/components/ui` and `/src/components/layout` while preserving the component props and API calls.
