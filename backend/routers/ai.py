import io
import os
import json
import time
import datetime
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Medication, DoseSchedule, PatientProfile, Appointment, CaregiverFollowup, User
from pydantic import BaseModel
from typing import Any, List, Optional
from dependencies import get_current_user, verify_profile_access
from PIL import Image

router = APIRouter()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB ceiling
CHUNK_SIZE = 64 * 1024             # 64 KB read buffer
AI_RATE_LIMIT_PER_MINUTE = 10
AI_RATE_WINDOW_SECONDS = 60

ENV = os.getenv("ENV", "development").lower()
DEMO_MODE = os.getenv("DEMO_MODE", "true" if ENV != "production" else "false").lower() == "true"

# In-memory sliding window rate limiter
_ai_rate_limits = defaultdict(list)


def check_ai_rate_limit(key: str) -> None:
    now = time.time()
    history = _ai_rate_limits[key]
    _ai_rate_limits[key] = [t for t in history if now - t < AI_RATE_WINDOW_SECONDS]
    if len(_ai_rate_limits[key]) >= AI_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI rate limit exceeded: maximum 10 requests per minute. Please try again later.",
        )
    _ai_rate_limits[key].append(now)


class ComparePrescriptionRequest(BaseModel):
    profile_id: int
    extracted_items: List[Any]


def _demo_prescription_fallback():
    return {
        "is_demo": True,
        "message": "Demo mode: GEMINI_API_KEY not configured. Showing sample extraction.",
        "extracted_items": [
            {
                "name": "Metformin",
                "dosage": "500mg",
                "frequency": "twice daily",
                "instructions": "With meals",
            },
            {
                "name": "Amlodipine",
                "dosage": "5mg",
                "frequency": "once daily",
                "instructions": "Morning",
            },
        ],
        "raw_ai_response": None,
    }


@router.post("/scan-prescription")
async def scan_prescription(
    image_file: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Rate limit per authenticated user
    check_ai_rate_limit(f"user_{current_user.id}")

    upload = image_file or file
    if not upload:
        return _demo_prescription_fallback()

    # 1. Bounded chunk read with 5 MB enforcement to prevent memory exhaustion
    contents = bytearray()
    while True:
        chunk = await upload.read(CHUNK_SIZE)
        if not chunk:
            break
        contents.extend(chunk)
        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of 5 MB ({len(contents)} bytes read)",
            )

    contents_bytes = bytes(contents)

    # 2. Magic byte signature validation (only JPEG and PNG accepted)
    is_jpeg = contents_bytes.startswith(b"\xff\xd8\xff")
    is_png = contents_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    is_demo_test_stub = DEMO_MODE and contents_bytes == b"fake-png-content"

    if not (is_jpeg or is_png or is_demo_test_stub):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format: only JPEG and PNG prescription images are accepted",
        )

    # 3. Image integrity verification using PIL
    if not is_demo_test_stub:
        try:
            img = Image.open(io.BytesIO(contents_bytes))
            img.verify()
            # Re-open for actual processing (verify closes/invalidates the image)
            img = Image.open(io.BytesIO(contents_bytes))
            if img.format not in ("JPEG", "PNG"):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Image format '{img.format}' is not supported. Use JPEG or PNG.",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed or corrupted image file",
            )

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return _demo_prescription_fallback()

    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "You are a medical assistant. Extract all medications from this prescription image. "
            "Return a JSON array where each item has: name, dosage, frequency, instructions. "
            "Only include real medications visible in the image. Never invent information. "
            "Return only valid JSON, no markdown."
        )
        response = model.generate_content([prompt, img])
        raw_text = response.text.strip()

        try:
            extracted = json.loads(raw_text)
        except json.JSONDecodeError:
            start = raw_text.find("[")
            end = raw_text.rfind("]") + 1
            if start != -1 and end > start:
                extracted = json.loads(raw_text[start:end])
            else:
                extracted = []

        return {
            "is_demo": False,
            "extracted_items": extracted,
            "raw_ai_response": raw_text,
        }

    except Exception:
        # Safe error response without internal traceback leakage
        return {
            "is_demo": True,
            "error": "AI prescription extraction service is temporarily unavailable",
            "extracted_items": [],
            "raw_ai_response": None,
        }


@router.post("/weekly-summary/{profile_id}")
async def weekly_summary(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    check_ai_rate_limit(f"user_{current_user.id}")
    # Get profile
    p_result = await db.execute(select(PatientProfile).where(PatientProfile.id == profile_id))
    profile = p_result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    await verify_profile_access(profile_id, current_user, db)

    # Get last 7 days doses
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    d_result = await db.execute(
        select(DoseSchedule)
        .join(Medication)
        .where(
            Medication.profile_id == profile_id,
            DoseSchedule.scheduled_time >= week_ago,
        )
    )
    doses = d_result.scalars().all()

    total = len(doses)
    taken = sum(1 for d in doses if d.status == "taken")
    missed = sum(1 for d in doses if d.status == "missed")
    pending = sum(1 for d in doses if d.status == "pending")
    not_confirmed = sum(1 for d in doses if d.status == "not_confirmed")
    adherence = round((taken / total * 100), 1) if total > 0 else 0

    # Query recorded reasons
    recorded_reasons = [d.reason_not_taken for d in doses if d.reason_not_taken]

    # Query pending caregiver follow-ups
    f_res = await db.execute(
        select(CaregiverFollowup)
        .join(DoseSchedule)
        .join(Medication)
        .where(
            Medication.profile_id == profile_id,
            CaregiverFollowup.status.in_(["accepted", "in_progress"]),
        )
    )
    pending_followups = f_res.scalars().all()

    # Query upcoming doctor appointments
    a_res = await db.execute(
        select(Appointment).where(
            Appointment.profile_id == profile_id,
            Appointment.date_time >= datetime.datetime.now(),
        ).order_by(Appointment.date_time.asc())
    )
    upcoming_appointments = a_res.scalars().all()

    reasons_str = ", ".join(set(recorded_reasons)) if recorded_reasons else "None recorded"
    followups_str = f"{len(pending_followups)} active follow-up(s)" if pending_followups else "No pending follow-ups"
    appts_str = ", ".join([f"{a.doctor_name} ({a.date_time.strftime('%b %d')})" for a in upcoming_appointments[:2]]) or "None scheduled"

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        # Rule-based summary
        summary = (
            f"Weekly Medication Summary for {profile.name}\n\n"
            f"• Total scheduled doses: {total}\n"
            f"• Taken: {taken} ({adherence}% adherence rate)\n"
            f"• Not confirmed / overdue: {not_confirmed}\n"
            f"• Missed doses: {missed}\n"
            f"• Recorded reasons: {reasons_str}\n"
            f"• Caregiver follow-ups: {followups_str}\n"
            f"• Upcoming appointments: {appts_str}\n\n"
        )
        if adherence >= 90:
            summary += "Excellent adherence this week! Continue following your current daily schedule."
        elif adherence >= 70:
            summary += "Good adherence overall. A few doses were delayed or unconfirmed—coordinating with your caregiver will help keep everything on schedule."
        else:
            summary += "Medication adherence requires attention. Please consult your family coordinator and doctor regarding any missed doses."

        return {
            "is_demo": True,
            "summary": summary,
            "stats": {
                "total": total,
                "taken": taken,
                "missed": missed,
                "pending": pending,
                "not_confirmed": not_confirmed,
                "adherence_percent": adherence,
                "recorded_reasons": list(set(recorded_reasons)),
                "pending_followups_count": len(pending_followups),
                "upcoming_appointments_count": len(upcoming_appointments),
            },
        }

    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = (
            f"Generate a compassionate weekly medication adherence summary for an elderly patient.\n"
            f"Patient: {profile.name}, Age: {profile.age}\n"
            f"Conditions: {', '.join(profile.medical_conditions or [])}\n"
            f"Doses this week - Total: {total}, Taken: {taken}, Missed: {missed}, "
            f"Pending: {pending}, Not confirmed: {not_confirmed}\n"
            f"Adherence rate: {adherence}%\n"
            f"Recorded reasons for unconfirmed doses: {reasons_str}\n"
            f"Caregiver follow-ups: {followups_str}\n"
            f"Upcoming doctor appointments: {appts_str}\n\n"
            f"Instructions:\n"
            f"- Write 3-4 sentences summarizing adherence, recorded reasons, and caregiver coordination.\n"
            f"- Strictly avoid medical advice or recommending dosage changes.\n"
            f"- Distinguish recorded clinical facts from coordination observations."
        )
        response = model.generate_content(prompt)

        return {
            "is_demo": False,
            "summary": response.text,
            "stats": {
                "total": total,
                "taken": taken,
                "missed": missed,
                "pending": pending,
                "not_confirmed": not_confirmed,
                "adherence_percent": adherence,
                "recorded_reasons": list(set(recorded_reasons)),
                "pending_followups_count": len(pending_followups),
                "upcoming_appointments_count": len(upcoming_appointments),
            },
        }
    except Exception as e:
        return {
            "is_demo": True,
            "error": str(e),
            "summary": f"Unable to generate AI summary. Adherence: {adherence}% ({taken}/{total} doses taken).",
            "stats": {
                "total": total,
                "taken": taken,
                "missed": missed,
                "pending": pending,
                "not_confirmed": not_confirmed,
                "adherence_percent": adherence,
            },
        }


@router.post("/compare-prescription")
async def compare_prescription(
    body: ComparePrescriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    check_ai_rate_limit(f"user_{current_user.id}")
    await verify_profile_access(body.profile_id, current_user, db)
    result = await db.execute(
        select(Medication).where(
            Medication.profile_id == body.profile_id,
            Medication.is_active == True
        )
    )
    existing_meds = result.scalars().all()
    existing_names = [m.name.lower() for m in existing_meds]

    comparison = []
    for raw_item in body.extracted_items:
        if isinstance(raw_item, dict):
            item_name = str(raw_item.get("name", "")).lower()
            item = raw_item
        else:
            item_name = str(raw_item).lower()
            item = {"name": str(raw_item), "dosage": "", "frequency": ""}

        is_existing = any(item_name in name or name in item_name for name in existing_names) if item_name else False
        comparison.append({
            "extracted": item,
            "is_existing": is_existing,
            "status": "existing" if is_existing else "new",
        })

    return {
        "is_demo": not bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here"),
        "comparison": comparison,
        "existing_medications": [
            {"id": m.id, "name": m.name, "dosage": m.dosage, "unit": m.unit}
            for m in existing_meds
        ],
    }
