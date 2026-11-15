# Triad Care — Security Audit & Authentication Architecture

**Project:** Triad Care  
**Branch:** `security/authentication-v1`  
**Status:** Architecture approved in principle — implementation pending final review  
**Document type:** Security audit and implementation specification  
**Scope:** Backend authentication, authorization, session management, data isolation and healthcare safety

---

## 1. Executive Summary

The initial security audit identified critical weaknesses in Triad Care's authentication and authorization architecture.

The most significant findings were:

- API endpoints did not consistently require authentication.
- User credentials were stored as plaintext passcodes.
- Frontend identity and role information could be restored from unverified local storage.
- Backend operations trusted client-supplied user IDs.
- Resource access did not consistently verify care-circle membership.
- Some medication operations bypassed the medication proposal and approval workflow.
- AI uploads lacked sufficient file-size and content validation.
- Security headers and rate limiting were incomplete.

The revised architecture introduces:

1. Argon2id password hashing.
2. Short-lived JWT access tokens.
3. Rotating, server-tracked refresh tokens.
4. Database-backed roles and care-circle membership.
5. Resource-level authorization.
6. Elderly patient sovereignty over active medication changes.
7. CSRF and Origin protection.
8. Strict separation of demo and real user data.
9. Real authentication-based integration tests.
10. Preservation of healthcare safety invariants.

**Important:** This document describes a proposed security architecture. It does not establish that these protections have already been implemented or independently tested.

## 2. Original Security Audit Findings

The initial audit covered 31 endpoints across nine routers.

| Finding | Severity | Description |
|---|---|---|
| Missing authentication | Critical | Endpoints did not consistently require an Authorization header. |
| Missing BOLA/IDOR protection | Critical | Users could potentially access resources belonging to another profile by supplying IDs. |
| Client-controlled identity | Critical | Some operations trusted user IDs supplied in request bodies. |
| Plaintext credentials | High | Demo passcodes were stored in plaintext. |
| Weak session management | High | No proper JWT, refresh-token or backend logout lifecycle. |
| Unverified frontend identity | High | Role and identity could be restored from localStorage. |
| Medication workflow bypass | High | Direct medication creation could bypass approval requirements. |
| Unbounded AI uploads | High | File uploads lacked adequate size and MIME validation. |
| Incomplete security headers | Medium | CSP, HSTS and other browser protections were incomplete. |
| Missing rate limits | Medium | Authentication and AI endpoints needed abuse protection. |

The original audit also identified identity-spoofing risks in:

- Dose confirmation.
- Caregiver follow-up claiming.
- Medication change approval.

These operations must derive the acting user's identity from the authenticated server-side session.

## 3. Authentication Architecture

### 3.1 Password hashing

Use Argon2id through `argon2-cffi`.

Proposed parameters:

```python
PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4
)
```

Requirements:

- Store only Argon2id password hashes.
- Never return password hashes in API responses.
- Never log plaintext credentials.
- Remove the legacy plaintext `passcode` field.
- Use secure password verification and hash rehashing when parameters change.
- Keep demo credentials isolated from production authentication.

### 3.2 Access tokens

Use signed JWT access tokens with HS256.

Minimum claims:

```json
{
  "sub": "1",
  "type": "access",
  "jti": "uuid4",
  "iat": 1794971200,
  "exp": 1794972100
}
```

Additional validation:

- Validate signature.
- Validate token type.
- Validate expiration.
- Validate issuer and audience.
- Require a strong server-side signing secret.
- Reject malformed and tampered tokens.

Access-token lifetime: **15 minutes**.

Roles and permissions must not be trusted from JWT claims. The backend must retrieve the current user and active membership from the database.

### 3.3 Current-user dependency

Every protected endpoint must use a shared authentication dependency.

The dependency must:

1. Extract the bearer token.
2. Validate its signature and claims.
3. Retrieve the user from the database.
4. Verify `is_active`.
5. Reject deleted or suspended users.
6. Supply the authenticated user to the endpoint.

The frontend must never be the authority for user identity.

### 3.4 Refresh tokens

Use cryptographically random opaque refresh tokens.

- Generate tokens using `secrets.token_urlsafe(48)`.
- Store only SHA-256 hashes in the database.
- Set a seven-day expiry.
- Store a token-family identifier.
- Revoke tokens on logout.
- Rotate refresh tokens after successful refresh.

The refresh token must be stored in an HttpOnly cookie, not localStorage.

## 4. Refresh-Token Rotation and Concurrency

### 4.1 Token-family model

Each login creates a unique `family_id`.

Each refresh-token record should include:

- Token ID.
- User ID.
- Token hash.
- Family ID.
- Parent token ID, where applicable.
- Creation timestamp.
- Expiration timestamp.
- Revocation timestamp.
- Successor token ID.
- Optional user-agent and IP metadata, subject to privacy and retention policies.

### 4.2 Atomic rotation

A refresh operation must be performed as a single database transaction.

Required sequence:

1. Receive the refresh cookie.
2. Hash the supplied token.
3. Retrieve its database record.
4. Verify that it exists, is unexpired and is not revoked.
5. Lock or serialize the relevant token-family operation.
6. Revoke the existing token.
7. Create exactly one successor token.
8. Associate the successor with the original token family.
9. Commit the transaction.
10. Return the new access token and refresh cookie.

### 4.3 Single-successor enforcement

The database must enforce one successor per parent refresh token.

A unique constraint or equivalent transactional enforcement must prevent two independent successor tokens from being created from the same parent.

For SQLite, use an appropriate serialized write transaction, such as `BEGIN IMMEDIATE`, where supported by the database access implementation.

### 4.4 Concurrent requests

The frontend should implement a single-flight refresh mechanism.

When multiple API requests receive a 401 response:

- Only one refresh request should be initiated.
- Other requests should wait for its result.
- Requests should retry once using the new access token.
- Failed refresh must end the session.
- Requests must not enter an infinite refresh loop.

Coordinate refresh behavior across browser tabs where practical.

Do not silently accept old refresh tokens through a grace period that permits multiple independent successor tokens.

If the refresh response is lost and the old token is subsequently reused, the session may need to be restarted through login. Security takes priority over transparent recovery.

### 4.5 Replay detection

If a revoked refresh token is reused:

- Treat it as a possible replay.
- Revoke all active tokens in the affected family.
- Reject the request with 401.
- Require fresh authentication.

Do not log raw refresh tokens.

## 5. ProfileMembership and Care-Circle Authorization

### 5.1 Membership model

Proposed model:

```python
class ProfileMembership(Base):
    __tablename__ = "profile_memberships"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(
        Integer,
        ForeignKey("patient_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String, nullable=False)
    relationship = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    permissions = Column(JSON, default=dict, nullable=False)
    joined_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
```

### 5.2 Required constraints

- Unique `(user_id, profile_id)` membership.
- Valid role values: `elderly`, `caregiver`, `family`.
- Valid membership statuses: `active`, `inactive`, `suspended`.
- Validated relationship values where applicable.
- Appropriate foreign-key constraints.
- No duplicate active membership records.

The implementation must inspect existing membership records before applying uniqueness constraints.

### 5.3 Fixed versus configurable permissions

**Role-fixed permissions:**

These cannot be overridden through configurable membership permissions:

- Only the elderly patient can approve or reject medication changes.
- Only the elderly patient can directly edit the active medication schedule.
- Family members cannot confirm medication doses.
- Only caregivers can claim and resolve caregiver follow-ups.
- Follow-up resolution cannot change medication status.

**Configurable permissions:**

These may support additional scoped coordination capabilities, such as:

- Appointment coordination.
- Viewing selected care information.
- Receiving notifications.
- Participating in care-circle updates.

Configurable permissions must never override role-fixed restrictions or grant access outside the member's assigned profile.

### 5.4 Universal membership validation

Every protected endpoint must verify active membership.

For profile-based endpoints:

- Resolve the requested profile.
- Check the authenticated user's active membership.
- Reject unauthorized access.

For individual resources:

- Resolve the resource's actual parent profile through its database relationship.
- Check membership in that parent profile.
- Never trust a client-supplied profile ID as proof of ownership.

This applies to:

- Medications.
- Dose schedules.
- Appointments.
- Caregiver follow-ups.
- Medication change requests.
- Notifications.
- Patient profile information.
- AI-generated records associated with a profile.

A revoked membership must stop granting access immediately, even if the user's access JWT has not expired.

## 6. Final Permission Matrix

All actions require active care-circle membership.

| Action | Elderly | Caregiver | Family |
|---|:---:|:---:|:---:|
| View patient profile | Yes | Yes | Yes |
| Edit patient profile | Yes | No | No |
| View medications | Yes | Yes | Yes |
| Directly add active medication | Yes | No | No |
| Directly edit/delete medication | Yes | No | No |
| Propose medication changes | Yes | Yes | Yes |
| Approve/reject medication changes | Yes | No | No |
| Confirm own dose | Yes | No | No |
| Confirm caregiver-observed dose | No | Yes* | No |
| Record skipped-dose reason | Yes | Yes* | No |
| Claim caregiver follow-up | No | Yes | No |
| Resolve assigned follow-up | No | Yes | No |
| View appointments | Yes | Yes | Yes |
| Coordinate appointments | Yes | Yes | Yes |
| View care-circle activity | Yes | Yes | Yes |

`*` Caregiver operations require active membership and appropriate assignment or authorization.

### 6.1 Medication sovereignty

Direct active medication creation, editing and deletion are restricted to the elderly patient.

Other care-circle members must use the medication change proposal workflow.

All proposals remain pending until the elderly patient explicitly approves them.

Approval must be enforced server-side.

No undefined `doctor` or `admin` role should be introduced as part of this implementation.

### 6.2 Dose confirmation semantics

Dose confirmation must distinguish three methods:

| Confirmation method | Meaning | Dose treatment |
|---|---|---|
| `patient_confirmed` | Patient confirms taking the medication | Taken |
| `caregiver_observed` | Caregiver personally witnessed the medication being taken | Taken, with caregiver attribution |
| `caregiver_reported` | Caregiver reports that the patient took medication but did not witness it | Not automatically taken |

Every confirmation must preserve:

- `confirmed_by_user_id`
- `confirmation_method`
- `confirmed_at`

A caregiver must not be able to mark a dose taken simply by claiming or resolving a follow-up.

## 7. Healthcare Safety Invariants

These are mandatory behavioral requirements.

1. Claiming a caregiver follow-up never marks a dose as taken.
2. Resolving a caregiver follow-up never marks a dose as taken.
3. Follow-up ownership and medication status remain independent.
4. `not_confirmed` must never be silently converted into `missed`.
5. Pending medication changes must not alter the active schedule.
6. Rejected medication changes must not alter the active schedule.
7. Only the elderly patient may approve or reject medication change proposals.
8. Caregiver-reported medication intake must remain distinguishable from observed intake.
9. Prescription OCR output must require human verification before saving.
10. AI must not advise users to take extra medication, stop medication or independently change medication schedules.
11. AI-generated summaries must use factual stored data and must not invent adherence statistics.
12. Uncertain prescription handwriting must be flagged for manual review.

## 8. Frontend Authentication Architecture

### 8.1 Access token storage

Access JWTs must remain in React application memory.

Never store access tokens in:

- localStorage.
- sessionStorage.
- Persistent browser databases.

### 8.2 Refresh cookie

Use a refresh cookie with:

- `HttpOnly`
- `SameSite=Lax`
- `Secure=true` in HTTPS deployments
- Explicit path and domain configuration

In production, prefer a `__Host-` cookie with `Path=/` and no `Domain` attribute.

### 8.3 Session restoration

On browser reload:

1. The application initializes without assuming the previous role is valid.
2. The frontend obtains a fresh CSRF token through the CSRF bootstrap endpoint.
3. It sends the refresh request with the HttpOnly cookie.
4. The backend validates and rotates the refresh token.
5. The backend returns a new access token.
6. The frontend stores the access token in memory.
7. The application retrieves the authenticated user through `/api/auth/me`.

If session restoration fails, the user returns to the login screen.

### 8.4 Axios behavior

The Axios client must:

- Attach the current access token to protected requests.
- Use credentials for refresh-cookie endpoints.
- Coordinate simultaneous refresh requests.
- Retry a failed protected request at most once.
- Clear in-memory session state after failed refresh.
- Never store access tokens persistently.

## 9. CSRF and Origin Protection

### 9.1 Protected cookie endpoints

At minimum:

- `/api/auth/refresh`
- `/api/auth/logout`

These endpoints must validate:

1. Request Origin against an explicit allowlist.
2. CSRF token.
3. Refresh-session validity where required.

CORS is not a replacement for CSRF protection.

### 9.2 CSRF token lifecycle

**Initial login**

- Validate the request Origin.
- Issue the refresh cookie.
- Return a cryptographically random CSRF token in the response body.
- Associate the CSRF token with the active session.

**Browser reload**

- The access token is absent because it existed only in memory.
- The frontend calls a CSRF bootstrap endpoint.
- The backend validates Origin and the refresh session.
- The endpoint returns a valid CSRF token without performing a refresh-token rotation.

**Refresh**

- Send the HttpOnly refresh cookie.
- Send the current CSRF token through `X-CSRF-Token`.
- Validate both before rotating the refresh token.
- Return a successor refresh cookie and rotate the CSRF token.

**Logout**

- Validate Origin and CSRF.
- Revoke the refresh-token family.
- Clear the refresh cookie.
- Clear in-memory access-token state.

Logout must remain possible when the access JWT has expired, provided the refresh session and CSRF validation remain valid.

**Invalid session**

- Reject the refresh operation.
- Clear the refresh cookie.
- End the browser session.

### 9.3 Environment-specific cookie settings

Local development may use HTTP with `Secure=false` only through explicit development configuration.

Production must use HTTPS and `Secure=true`.

Do not silently disable Origin or CSRF validation in production.

## 10. Demo Mode and Data Isolation

Triad Care must retain a convenient synthetic demo experience for hackathon judges.

### 10.1 Demo mode configuration

- `DEMO_MODE=false` by default in production.
- Demo login returns HTTP 404 when disabled.
- Demo credentials must not be accepted through production login.
- Demo accounts must use hashed credentials.
- Public demo credentials must be documented as synthetic-only, if exposed at all.

### 10.2 Data isolation

Demo accounts must only access demo profiles.

Real accounts must not access demo profiles through normal membership operations.

Demo accounts must not join real profiles.

The backend must enforce this isolation at the database access and authorization layers, not just through frontend navigation.

All public demo data must be synthetic. No actual patient records or private medical information should be used.

## 11. Database Migration Strategy

Use Alembic with explicit migrations.

Do not perform ad hoc schema modifications at application startup.

### 11.1 Migration plan

| Step | Migration work |
|---|---|
| 001 | Add `hashed_password`, `is_active`, `is_demo` to users |
| 002 | Create refresh-token table and family relationships |
| 003 | Add membership status, relationship, permissions and timestamps |
| 004 | Add membership uniqueness and role/status validation |
| 005 | Add dose confirmation method and audit fields |
| 006 | Hash existing demo passcodes and remove plaintext `passcode` |

### 11.2 Migration safeguards

Before migration:

1. Back up the existing database.
2. Inspect existing users and membership records.
3. Identify duplicate memberships.
4. Verify existing demo accounts and profile relationships.
5. Test migrations on a copy of the database.

During migration:

1. Hash existing credentials using Argon2id.
2. Verify hashes.
3. Create refresh-token structures.
4. Upgrade membership records.
5. Add constraints.
6. Remove plaintext credentials using SQLite batch table recreation.

After migration:

- Verify that no plaintext passcode column remains.
- Verify all users and memberships remain intact.
- Verify medications, doses, appointments and notifications remain intact.
- Run upgrade and rollback tests.
- Confirm that application startup does not perform schema alterations.

The migration must not silently discard existing application data.

## 12. AI Upload Security

AI file upload endpoints must implement:

- Maximum upload size of 5 MB.
- MIME allowlisting.
- Actual file-content/signature validation.
- Image decoding and validation.
- Streaming or bounded reads rather than unrestricted full-file reads.
- Request timeouts.
- Per-user and per-IP rate limiting.
- Appropriate error handling.
- Protection against excessive Gemini API usage.

Do not trust a client-provided MIME type by itself.

Uploaded files must not be retained longer than required by the product workflow.

## 13. Security Headers and API Configuration

Review and configure:

- Content-Security-Policy.
- Strict-Transport-Security on HTTPS deployments.
- X-Content-Type-Options.
- Frame protection using `frame-ancestors` or appropriate X-Frame-Options.
- Referrer-Policy.
- Permissions-Policy.
- Explicit CORS allowlist.
- Request-size limits.
- Authentication and AI endpoint rate limits.

CSP must be compatible with the actual frontend and Gemini integrations. Do not introduce a permissive wildcard policy merely to make the application work.

HSTS must only be enabled for HTTPS deployments.

## 14. Security Testing Strategy

### 14.1 Baseline regression tests

Preserve all 33 existing baseline tests in:

- `backend/test_caresync.py`
- `backend/test_independent_qa.py`

Adapt fixtures to authenticate through real login or demo-login flows.

Do not globally bypass authentication using dependency overrides.

### 14.2 New security test suite

Create:

`backend/test_security_upgrade.py`

Required tests:

**Credentials**
- Argon2id hash generation and verification.
- No plaintext passcodes in database schema.
- No password hashes in API responses.

**Authentication**
- Unauthenticated request rejection.
- Expired JWT rejection.
- Tampered JWT rejection.
- Invalid token-type rejection.
- Inactive user rejection.

**Refresh-token security**
- Successful rotation.
- Old token rejection.
- Single-successor enforcement.
- Concurrent refresh handling.
- Token-family replay detection.
- Family-wide revocation.
- Logout revocation.

**CSRF**
- Missing CSRF token rejected.
- Invalid CSRF token rejected.
- Invalid Origin rejected.
- CSRF token rotation.
- CSRF bootstrap behavior.
- Logout with expired access token.

**BOLA/IDOR**
- Cross-profile access rejected.
- Unauthorized resource IDs rejected.
- Medication access isolation.
- Dose access isolation.
- Appointment access isolation.
- Follow-up access isolation.
- Medication-change access isolation.
- Notification access isolation.

**Identity spoofing**
- Client-supplied `user_id` rejected.
- Forged `confirmed_by_user_id` rejected.
- Forged reviewer identity rejected.
- Caller cannot claim another caregiver's identity.

**Role enforcement**
- Family cannot directly modify active medication.
- Caregiver cannot approve medication changes.
- Family cannot confirm doses.
- Only assigned caregivers can resolve follow-ups.
- Elderly patient sovereignty is preserved.

**Healthcare safety**
- Follow-up claiming does not change dose status.
- Follow-up resolution does not change dose status.
- Caregiver-reported intake does not automatically mark a dose taken.
- Pending medication changes do not alter active schedules.
- Rejected medication changes do not alter active schedules.

**Demo isolation**
- Demo login unavailable when `DEMO_MODE=false`.
- Demo users cannot access real profiles.
- Real users cannot access demo profiles.
- Demo credentials cannot authenticate through production login.

**Upload security**
- Oversized upload rejected.
- Invalid MIME rejected.
- Invalid file content rejected.
- Rate limiting enforced.

### 14.3 Acceptance criteria

The security upgrade is not considered complete until:

- All 33 baseline tests pass.
- All new security tests pass.
- Frontend production build succeeds.
- Database migration tests pass.
- Refresh-token concurrency tests pass.
- Cross-profile isolation tests pass.
- Existing healthcare safety invariants remain intact.
- Demo access remains functional in the isolated demo environment.

These are acceptance targets, not claims of completed testing.

## 15. Implementation Phases

Implementation should proceed in isolated, reviewable phases.

| Phase | Scope |
|---|---|
| 1 | Database migrations, Argon2id, membership and refresh-token models |
| 2 | Authentication endpoints, JWT validation and session lifecycle |
| 3 | Backend authorization and care-circle resource isolation |
| 4 | Frontend authentication and session restoration |
| 5 | Adversarial testing and regression validation |
| 6 | Upload hardening, rate limiting and security headers |

Each phase must be tested before proceeding to the next.

### Branch protection

All work must remain on:

`security/authentication-v1`

Do not merge into `main` until final review and explicit approval.

The existing hackathon demo on `main` must remain unaffected.

## 16. Limitations and Production Readiness

Even after implementing this architecture, Triad Care must not automatically be described as:

- HIPAA compliant.
- Production-ready for clinical use.
- A certified medical device.
- A replacement for professional medical advice.

Production deployment would require additional security review, privacy assessment, operational monitoring, backup and recovery procedures, incident response planning, and applicable legal and regulatory review.

Only synthetic demo data should be used during hackathon evaluation.

---

## 17. Current Review Status

| Item | Status |
|---|---|
| Original security audit findings | Documented |
| Argon2id authentication design | Specified |
| JWT access-token design | Specified |
| Refresh-token rotation | Specified |
| Membership and BOLA protection | Specified |
| Medication permission matrix | Specified |
| Dose confirmation semantics | Specified |
| CSRF lifecycle | Specified |
| Demo isolation | Specified |
| Migration strategy | Specified |
| Adversarial test plan | Specified |
| Application source changes | Not authorized |
| Database changes | Not authorized |
| Existing test changes | Not authorized |
| Merge into `main` | Not authorized |

**Final status: Architecture specification ready for review.**

No implementation should begin until the project owner explicitly approves this document.
