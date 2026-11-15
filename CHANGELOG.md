# Triad Care Development Changelog

All notable changes, bug fixes, architecture decisions, and test runs for Triad Care (formerly CareSync) are documented in this file.

---

## [1.2.0] — 2026-11-15: Official Project Rebranding to Triad Care

### Summary
Full project-wide branding update transitioning the application identity from **CareSync** to **Triad Care**.
- **Product Name:** Triad Care
- **Tagline:** Care that connects. Responsibility that follows.
- **Description:** An AI-powered elderly care coordination and accountability platform connecting elderly individuals, caregivers, and family members.

### Changes Applied
- **Frontend Identity & UI Branding:**
  - `frontend/index.html`: Updated browser title to `Triad Care — Care that connects. Responsibility that follows.`
  - `frontend/package.json`: Updated package name to `triad-care`.
  - `LoginPage.tsx`: Updated brand header to **Triad Care**, description, and tagline `"Care that connects. Responsibility that follows."`
  - `Sidebar.tsx`: Updated logo icon to `T` and sidebar brand title to `Triad Care`.
  - `TopBar.tsx`: Updated fallback brand title to `Triad Care`.
  - `FamilyDashboard.tsx`: Updated footer quote to `"Care that connects. Responsibility that follows."`
  - `PrescriptionScanner.tsx`: Updated verification guidance to reference Triad Care.
  - `WeeklySummary.tsx`: Updated medical disclaimer to reference Triad Care.
- **Backend Identity:**
  - `backend/main.py`: Updated FastAPI application title to `Triad Care API`, description, and root `/` route response.
  - `backend/test_caresync.py` & `backend/test_independent_qa.py`: Updated suite header docstrings to Triad Care.
- **Documentation & Environment:**
  - Updated `README.md`, `PROJECT_CONTEXT.txt`, `QA_AUDIT.md`, `INDEPENDENT_QA_REVIEW.md`, and `.env.example` with Triad Care branding.
- **Preserved Internal Technical Identifiers (Zero Regression Policy):**
  - Preserved internal SQLite database filename (`backend/caresync.db`) and baseline test suite filename (`backend/test_caresync.py`) to maintain compatibility with existing deployment scripts and automated CI.
  - Preserved business logic, role permissions, medication workflows, caregiver accountability, AI behavior, and healthcare safety constraints.

---

## [1.0.0] — 2026-11-15: Initial MVP Build, QA Audit & Safety Verification

### Summary
Initial implementation, comprehensive QA testing, and safety hardening of the CareSync full-stack elderly care platform.

### Added
- **Backend Architecture (`backend/`):**
  - FastAPI application with CORS middleware, lifespan events, and modular routing.
  - SQLAlchemy async data layer with SQLite backend (`backend/caresync.db`).
  - 10 ORM Models in `backend/models.py`: `User`, `PatientProfile`, `ProfileMembership`, `Medication`, `DoseSchedule`, `Appointment`, `Notification`, `CaregiverFollowup`, `Prescription`, `MedicationChangeRequest`.
  - Pydantic v2 schemas for all inputs and response models (`backend/schemas.py`).
  - Synthetic demo seeder (`backend/seed.py`) populating Meera Sharma, Riya Patel, Arjun Sharma, chronic conditions, active prescriptions, appointments, and pending change requests.
  - 9 API Routers in `backend/routers/`:
    - `auth.py`: Demo user listing and 4-digit passcode login.
    - `patients.py`: Patient profile retrieval and membership associations.
    - `medications.py`: Medication CRUD and today's schedule generation.
    - `doses.py`: Today's dose schedule, dose confirmation, and reason logging.
    - `followups.py`: Caregiver "I'm handling it" claim, tracking, and resolution.
    - `appointments.py`: Doctor appointments CRUD.
    - `changes.py`: Family medication change proposals and elderly approval workflow.
    - `notifications.py`: In-app notification center.
    - `ai.py`: Gemini Vision OCR extraction, medication diffing, and weekly health digest.
- **Frontend Architecture (`frontend/`):**
  - React 19 + TypeScript + Vite 8 application with custom Tailwind theme.
  - Decoupled API service layer in `frontend/src/api/` (Axios).
  - TypeScript contracts in `frontend/src/types/index.ts`.
  - Global authentication context in `frontend/src/store/authStore.tsx` with instant demo switcher.
  - Reusable UI component library (`frontend/src/components/ui/`): `Button`, `Card`, `Badge`, `Modal`, `StatusBadge`, `LoadingSpinner`, `EmptyState`.
  - Layout components (`frontend/src/components/layout/`): `AppLayout`, `Sidebar`, `TopBar`, `NotificationBell`.
  - Domain-specific components:
    - Medications: `DoseCard`, `MedicationCard`, `MedicationForm`, `RecordReasonModal`.
    - Followups: `ClaimFollowupModal`, `FollowupCard`.
    - Appointments: `AppointmentCard`, `AppointmentForm`.
    - Changes: `ChangeRequestCard`, `ChangeRequestForm`.
    - AI: `PrescriptionScanner`, `WeeklySummary`.
  - Role-specific pages:
    - Elderly: `ElderlyDashboard`, `ElderlyMedications`, `ElderlyAppointments`.
    - Caregiver: `CaregiverDashboard`, `CaregiverFollowups`, `CaregiverPatients`.
    - Family: `FamilyDashboard`, `FamilyMedications`, `FamilyAppointments`, `FamilyChanges`.
    - Shared: `AIFeatures`, `NotificationsPage`, `LoginPage`.
- **Automated Test Suite (`backend/test_caresync.py`):**
  - 20 comprehensive Pytest tests covering all 12 QA scenarios and 8 healthcare safety rules.

### Fixed & Hardened During Audit
- **SQLAlchemy MissingGreenlet Error in `changes.py`:**
  - *Root Cause:* Calling `await db.refresh(req)` inside `review_change` expired the eager-loaded relationships `req.medication` and `req.requested_by_user`. When FastAPI serialized the Pydantic response, it attempted an async lazy-load outside an async greenlet.
  - *Fix:* Replaced `db.refresh(req)` with an explicit query using `selectinload()`.
- **Medication Deletion Leak in Schedules:**
  - *Root Cause:* Queries in `medications.py` and `doses.py` did not explicitly check `Medication.is_active == True`. Deactivated medications could still show pending doses on today's schedule.
  - *Fix:* Added `Medication.is_active == True` filter to both `today_schedule` and `get_today_doses`.
- **Tailwind CSS v4 to v3 Compatibility:**
  - *Root Cause:* Initial scaffold installed Tailwind v4 which deprecated `@tailwind` directives.
  - *Fix:* Installed `tailwindcss@^3.4.17` with `postcss.config.js` to ensure reliable compilation across all platforms.
- **Button Component Outline Variant:**
  - *Root Cause:* TypeScript flagged `'outline'` variant as missing from `Variant` type.
  - *Fix:* Added `'outline'` to `Variant` union and defined styled classes in `Button.tsx`.
- **EmptyState Action Prop Compatibility:**
  - *Root Cause:* TypeScript prevented passing `{ label, onClick }` objects to `EmptyState`.
  - *Fix:* Enhanced `EmptyStateProps.action` union to accept both `ReactNode` and `{ label: string; onClick: () => void }`.
- **Notification Client Export Aliases:**
  - *Root Cause:* Pages called `markAsRead` and `markAllAsRead`, whereas the client exported `markNotificationRead` and `markAllRead`.
  - *Fix:* Added export aliases in `frontend/src/api/notifications.ts`.

### Tests Performed
- **Backend Pytest Suite:** 20 tests executed. 20 PASSED (100% pass rate).
- **Critical Safety Assertions:**
  - Follow-up claim does not mark dose as taken: PASSED.
  - Follow-up resolution does not mark dose as taken: PASSED.
  - Unconfirmed dose is not classified as missed: PASSED.
  - Pending change request does not alter active medication: PASSED.
  - Rejected change request does not alter active medication: PASSED.
  - Approved change request updates medication strictly upon approval: PASSED.
- **Frontend Production Build:** `tsc -b && vite build` completed in 1.11s with 0 errors.

### Known Limitations / Remaining Work
- Live Gemini Vision API calls require setting `GEMINI_API_KEY` in `backend/.env`. In its absence, the built-in demo fallback mode functions with simulated results.
- Automated email dispatch via Resend is structured in configuration but disabled by default to avoid claiming emails were dispatched locally without credentials.

---

## [1.1.0] — 2026-11-15: Independent QA Audit, Adversarial Hardening & Security Remediation

### Summary
Independent verification of previous QA claims, challenge of healthcare safety guarantees under adversarial API conditions, remediation of security data leaks and missing authorization checks, creation of `INDEPENDENT_QA_REVIEW.md`, and expansion of test suite from 20 to 33 automated tests.

### Added
- **Adversarial QA Suite (`backend/test_independent_qa.py`):**
  - 13 new automated tests verifying role boundaries, passcode redaction, safety invariants under hostile calls, AI fallback honesty, entity boundary handling, and data persistence across process restarts.
- **Independent QA Report (`INDEPENDENT_QA_REVIEW.md`):**
  - Detailed report covering claims verified vs. not verified, security risks, AI reliability, deployment blockers, and hackathon presentation readiness.

### Fixed & Hardened
- **Passcode Redaction in API Responses:**
  - Redacted plaintext passcodes from `UserOut` schema in `backend/schemas.py`.
  - Updated frontend `types/index.ts` to make `passcode?: string` optional. Plaintext passcodes are no longer leaked via `/api/auth/demo-users` or `/api/auth/login`.
- **Elderly Sovereignty Enforcement on Medication Changes:**
  - Added role check in `backend/routers/changes.py` ensuring only `user.role == "elderly"` can approve or reject changes. Non-elderly callers receive `403 Forbidden`.
  - Added idempotency guard preventing already-reviewed requests from being altered (`400 Bad Request`).
- **Caregiver Role Enforcement on Follow-Up Claims:**
  - Added role validation in `backend/routers/followups.py` ensuring only `user.role == "caregiver"` can claim follow-ups (`403 Forbidden` for other roles).
  - Enforced allowed action sets (`calling`, `going_to_check`, `unavailable`) and status updates.
  - Guarded against claiming follow-ups on already-taken doses (`400 Bad Request`).
- **AI Weekly Summary Context Enhancement:**
  - Enhanced `backend/routers/ai.py` weekly summary to query and aggregate `CaregiverFollowup` and `Appointment` data alongside doses and recorded reasons.
- **AI Prescription Comparison Type Safety:**
  - Added string/dict type checking in `compare-prescription` endpoint to prevent `AttributeError` crashes on raw string input.
- **CORS Configuration Hardening:**
  - Updated `backend/main.py` CORS setup to use an explicit allowed origin whitelist rather than combining wildcard with credentials.
- **AI Syntax Fix:**
  - Cleaned up duplicated, unindented dictionary keys in `backend/routers/ai.py`.

### Tests Performed
- **Baseline Test Suite (`test_caresync.py`):** 20 / 20 PASSED.
- **Adversarial Test Suite (`test_independent_qa.py`):** 13 / 13 PASSED.
- **Combined Backend Test Suite:** 33 / 33 PASSED (100%).
- **Data Persistence Verification:** Backend restarted; SQLite persistence verified across process lifecycles.
- **Frontend Production Build:** `tsc -b && vite build` succeeded in 1.42s with 0 errors.

