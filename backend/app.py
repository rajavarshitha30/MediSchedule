
from pathlib import Path
from datetime import datetime
import os
import time
from typing import Any
from fastapi import Body
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client import QdrantClient
from fastapi import Body
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import sqlite3
from fastapi.staticfiles import StaticFiles
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from qdrant_client import QdrantClient
from fastembed import TextEmbedding
from typing import Any
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from qdrant_client.models import Filter, FieldCondition, MatchValue
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="MediSchedule AI Backend",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://medischedule2.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {
        "message": "MediSchedule AI Backend is running!",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "online",
        "qdrant": "connected" if qdrant is not None else "disconnected",
        "database": "connected",
        "lyzr_chat_configured": bool(os.getenv("LYZR_API_KEY")),
        "lyzr_voice_configured": bool(
            os.getenv("LYZR_VOICE_API_KEY") or os.getenv("LYZR_API_KEY")
        )
    }
app.mount(
    "/static",
    StaticFiles(directory=str(PROJECT_ROOT / "frontend")),
    name="static"
)

@app.get("/voice-ui")
def voice_ui():
    return FileResponse(PROJECT_ROOT / "frontend" / "index.html")


load_dotenv(PROJECT_ROOT / ".env", override=True)

LYZR_API_KEY = os.getenv("LYZR_API_KEY", "").strip()
LYZR_AGENT_ID = os.getenv("LYZR_AGENT_ID", "").strip()

LYZR_VOICE_AGENT_ID = os.getenv(
    "LYZR_VOICE_AGENT_ID", ""
).strip()

LYZR_VOICE_API_KEY = (
    os.getenv("LYZR_VOICE_API_KEY", "").strip()
    or LYZR_API_KEY
)

LYZR_URL = (
    "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"
)

VOICE_API_URL = (
    "https://voice-livekit.studio.lyzr.ai/v1/sessions/start"
)

VOICE_END_API_URL = (
    "https://voice-livekit.studio.lyzr.ai/v1/sessions/end"
)

DATABASE = str(BACKEND_DIR / "medischedule.db")
QDRANT_PATH = str(BACKEND_DIR / "qdrant_memory")

# =========================================================
# QDRANT
# =========================================================

try:
    qdrant = QdrantClient(path=QDRANT_PATH)

    embedding_model = TextEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )

    print("Qdrant connected successfully!")

except Exception as exc:
    qdrant = None
    embedding_model = None

    print(f"Qdrant initialization failed: {exc}")


# =========================================================
# SQLITE DATABASE
# =========================================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            phone TEXT,
            email TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            available_days TEXT,
            available_time TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Booked',
            created_at TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(doctor_id) REFERENCES doctors(id)
        )
    """)

    connection.commit()
    connection.close()


initialize_database()


# =========================================================
# DATA MODELS
# =========================================================

class PatientCreate(BaseModel):
    name: str
    age: int
    phone: str
    email: str


class DoctorCreate(BaseModel):
    name: str
    specialization: str
    available_days: str
    available_time: str


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: str
    appointment_time: str
    reason: str = ""


class RescheduleRequest(BaseModel):
    appointment_date: str
    appointment_time: str


class AIRequest(BaseModel):
    user_id: str
    message: str


class VoiceSessionRequest(BaseModel):
    user_identity: str = "patient_demo_001"
    room_name: str | None = None


class EndVoiceSessionRequest(BaseModel):
    room_name: str


# =========================================================
# HOME AND HEALTH
# =========================================================



@app.get("/check-config")
def check_config():
    return {
        "env_file_path": str(PROJECT_ROOT / ".env"),
        "env_file_exists": (
            PROJECT_ROOT / ".env"
        ).is_file(),
        "api_key_loaded": bool(LYZR_API_KEY),
        "chat_agent_id_loaded": bool(LYZR_AGENT_ID),
        "voice_api_key_loaded": bool(LYZR_VOICE_API_KEY),
        "voice_agent_id_loaded": bool(LYZR_VOICE_AGENT_ID)
    }


# =========================================================
# PATIENT REGISTRATION
# =========================================================

@app.post("/patients")
def create_patient(patient: PatientCreate):
    connection = get_db()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO patients (name, age, phone, email)
            VALUES (?, ?, ?, ?)
        """, (
            patient.name,
            patient.age,
            patient.phone,
            patient.email
        ))

        patient_id = cursor.lastrowid
        connection.commit()

        return {
            "message": "Patient registered successfully",
            "patient_id": patient_id,
            "patient": patient.model_dump()
        }

    finally:
        connection.close()


@app.get("/patients")
def get_patients():
    connection = get_db()

    try:
        rows = connection.execute(
            "SELECT * FROM patients ORDER BY id"
        ).fetchall()

        return {
            "count": len(rows),
            "patients": [dict(row) for row in rows]
        }

    finally:
        connection.close()


# =========================================================
# DOCTOR MANAGEMENT
# =========================================================

@app.post("/doctors")
def create_doctor(doctor: DoctorCreate):
    connection = get_db()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO doctors
            (name, specialization, available_days, available_time)
            VALUES (?, ?, ?, ?)
        """, (
            doctor.name,
            doctor.specialization,
            doctor.available_days,
            doctor.available_time
        ))

        doctor_id = cursor.lastrowid
        connection.commit()

        return {
            "message": "Doctor added successfully",
            "doctor_id": doctor_id,
            "doctor": doctor.model_dump()
        }

    finally:
        connection.close()


@app.get("/doctors")
def get_doctors():
    connection = get_db()

    try:
        rows = connection.execute(
            "SELECT * FROM doctors ORDER BY id"
        ).fetchall()

        return {
            "count": len(rows),
            "doctors": [dict(row) for row in rows]
        }

    finally:
        connection.close()


# =========================================================
# BOOK APPOINTMENT
# =========================================================

@app.post("/appointments")
def book_appointment(appointment: AppointmentCreate):
    connection = get_db()

    try:
        cursor = connection.cursor()

        patient = cursor.execute(
            "SELECT * FROM patients WHERE id = ?",
            (appointment.patient_id,)
        ).fetchone()

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found"
            )

        doctor = cursor.execute(
            "SELECT * FROM doctors WHERE id = ?",
            (appointment.doctor_id,)
        ).fetchone()

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found"
            )

        existing = cursor.execute("""
            SELECT * FROM appointments
            WHERE doctor_id = ?
              AND appointment_date = ?
              AND appointment_time = ?
              AND status = 'Booked'
        """, (
            appointment.doctor_id,
            appointment.appointment_date,
            appointment.appointment_time
        )).fetchone()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Doctor is already booked at this time"
            )

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute("""
            INSERT INTO appointments
            (
                patient_id,
                doctor_id,
                appointment_date,
                appointment_time,
                reason,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment.patient_id,
            appointment.doctor_id,
            appointment.appointment_date,
            appointment.appointment_time,
            appointment.reason,
            "Booked",
            created_at
        ))

        appointment_id = cursor.lastrowid
        connection.commit()

        return {
            "message": "Appointment booked successfully",
            "appointment_id": appointment_id,
            "appointment": appointment.model_dump()
        }

    finally:
        connection.close()


# =========================================================
# VIEW APPOINTMENTS
# =========================================================

@app.get("/appointments")
def get_appointments():
    connection = get_db()

    try:
        rows = connection.execute("""
            SELECT
                appointments.id,
                patients.name AS patient_name,
                doctors.name AS doctor_name,
                doctors.specialization,
                appointments.appointment_date,
                appointments.appointment_time,
                appointments.reason,
                appointments.status
            FROM appointments
            JOIN patients
                ON appointments.patient_id = patients.id
            JOIN doctors
                ON appointments.doctor_id = doctors.id
            ORDER BY
                appointments.appointment_date,
                appointments.appointment_time
        """).fetchall()

        return {
            "count": len(rows),
            "appointments": [dict(row) for row in rows]
        }

    finally:
        connection.close()


# =========================================================
# CANCEL APPOINTMENT
# =========================================================

@app.delete("/appointments/{appointment_id}")
def cancel_appointment(appointment_id: int):
    connection = get_db()

    try:
        cursor = connection.cursor()

        appointment = cursor.execute(
            "SELECT * FROM appointments WHERE id = ?",
            (appointment_id,)
        ).fetchone()

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found"
            )

        cursor.execute("""
            UPDATE appointments
            SET status = 'Cancelled'
            WHERE id = ?
        """, (appointment_id,))

        connection.commit()

        return {
            "message": "Appointment cancelled successfully",
            "appointment_id": appointment_id
        }

    finally:
        connection.close()


# =========================================================
# RESCHEDULE APPOINTMENT
# =========================================================

@app.put("/appointments/{appointment_id}/reschedule")
def reschedule_appointment(
    appointment_id: int,
    request: RescheduleRequest
):
    connection = get_db()

    try:
        cursor = connection.cursor()

        appointment = cursor.execute("""
            SELECT * FROM appointments
            WHERE id = ? AND status = 'Booked'
        """, (appointment_id,)).fetchone()

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Active appointment not found"
            )

        conflict = cursor.execute("""
            SELECT * FROM appointments
            WHERE doctor_id = ?
              AND appointment_date = ?
              AND appointment_time = ?
              AND status = 'Booked'
              AND id != ?
        """, (
            appointment["doctor_id"],
            request.appointment_date,
            request.appointment_time,
            appointment_id
        )).fetchone()

        if conflict:
            raise HTTPException(
                status_code=409,
                detail="New appointment time is already booked"
            )

        cursor.execute("""
            UPDATE appointments
            SET appointment_date = ?,
                appointment_time = ?
            WHERE id = ?
        """, (
            request.appointment_date,
            request.appointment_time,
            appointment_id
        ))

        connection.commit()

        return {
            "message": "Appointment rescheduled successfully",
            "appointment_id": appointment_id,
            "new_date": request.appointment_date,
            "new_time": request.appointment_time
        }

    finally:
        connection.close()


# =========================================================
# LYZR CHAT AGENT
# =========================================================

@app.post("/ai-assistant")
def ai_assistant(request: AIRequest):
    if not LYZR_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="LYZR_API_KEY is missing"
        )

    if not LYZR_AGENT_ID:
        raise HTTPException(
            status_code=500,
            detail="LYZR_AGENT_ID is missing"
        )

    message = f"""
You are MediSchedule AI, a patient appointment scheduling assistant.

Help patients find doctors and schedule, reschedule, or cancel
appointments. Ask for missing information.

Do not diagnose diseases, recommend medicines, or provide treatment.
Never claim an appointment is booked unless the scheduling system
has actually confirmed the booking.

Patient message:
{request.message}

Respond clearly and professionally.
"""

    payload = {
        "user_id": request.user_id,
        "agent_id": LYZR_AGENT_ID,
        "session_id": f"session_{request.user_id}",
        "message": message
    }

    try:
        response = requests.post(
            LYZR_URL,
            headers={
                "x-api-key": LYZR_API_KEY,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )

        try:
            result = response.json()
        except ValueError:
            result = {"detail": response.text}

        return {
            "status_code": response.status_code,
            "response": result
        }

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        )


@app.get("/test-lyzr")
def test_lyzr():
    if not LYZR_API_KEY:
        return {"error": "LYZR_API_KEY is missing"}

    if not LYZR_AGENT_ID:
        return {"error": "LYZR_AGENT_ID is missing"}

    payload = {
        "user_id": "test_patient_001",
        "agent_id": LYZR_AGENT_ID,
        "session_id": "test_session_001",
        "message": (
            "A patient needs a doctor appointment tomorrow evening. "
            "Ask for any missing scheduling information. "
            "Do not diagnose or provide medical treatment."
        )
    }

    try:
        response = requests.post(
            LYZR_URL,
            headers={
                "x-api-key": LYZR_API_KEY,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )

        try:
            result = response.json()
        except ValueError:
            result = {"detail": response.text}

        return {
            "status_code": response.status_code,
            "lyzr_response": result
        }

    except requests.RequestException as exc:
        return {"error": str(exc)}


@app.get("/verify-lyzr-agent")
def verify_lyzr_agent():
    if not LYZR_API_KEY or not LYZR_AGENT_ID:
        return {
            "error": "Chat Lyzr credentials are missing"
        }

    url = (
        "https://agent-prod.studio.lyzr.ai/v3/agents/"
        f"{LYZR_AGENT_ID}"
    )

    try:
        response = requests.get(
            url,
            headers={"x-api-key": LYZR_API_KEY},
            timeout=20
        )

        try:
            result = response.json()
        except ValueError:
            result = {"detail": response.text}

        return {
            "status_code": response.status_code,
            "agent_details": result
        }

    except requests.RequestException as exc:
        return {"error": str(exc)}


# =========================================================
# LYZR VOICE AGENT: START SESSION
# =========================================================

@app.post("/start-voice-session")
def start_voice_session(request: VoiceSessionRequest):
    if not LYZR_VOICE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail=(
                "Voice API key is missing. "
                "Check LYZR_VOICE_API_KEY in the project-root .env."
            )
        )

    if not LYZR_VOICE_AGENT_ID:
        raise HTTPException(
            status_code=500,
            detail=(
                "Voice Agent ID is missing. "
                "Check LYZR_VOICE_AGENT_ID in the project-root .env."
            )
        )

    payload = {
        "agentId": LYZR_VOICE_AGENT_ID,
        "userIdentity": request.user_identity
    }

    if request.room_name:
        payload["roomName"] = request.room_name

    try:
        response = requests.post(
            VOICE_API_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": LYZR_VOICE_API_KEY
            },
            json=payload,
            timeout=30
        )

        try:
            result = response.json()
        except ValueError:
            result = {"detail": response.text}

        if not response.ok:
            raise HTTPException(
                status_code=response.status_code,
                detail=result
            )

        return result

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        )


# =========================================================
# LYZR VOICE AGENT: END SESSION
# =========================================================

@app.post("/end-voice-session")
def end_voice_session(request: EndVoiceSessionRequest):
    if not LYZR_VOICE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Voice API key is missing"
        )

    try:
        response = requests.post(
            VOICE_END_API_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": LYZR_VOICE_API_KEY
            },
            json={"roomName": request.room_name},
            timeout=30
        )

        try:
            result = response.json()
        except ValueError:
            result = {"detail": response.text}

        if not response.ok:
            raise HTTPException(
                status_code=response.status_code,
                detail=result
            )

        return result

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        )

# =========================================================
# OMI WEBHOOKS AND QDRANT VOICE MEMORY
# =========================================================

OMI_COLLECTION = "omi_memories"


def ensure_omi_collection():
    """Create the Omi memory collection if it does not exist."""
    if qdrant is None or embedding_model is None:
        raise HTTPException(
            status_code=503,
            detail="Qdrant or the embedding model is unavailable"
        )

    if not qdrant.collection_exists(OMI_COLLECTION):
        qdrant.create_collection(
            collection_name=OMI_COLLECTION,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )


def extract_omi_text(payload):
    """Extract transcript text from common Omi webhook formats."""
    if isinstance(payload, str):
        return payload.strip()

    if isinstance(payload, list):
        segments = payload
        extra_text = ""
    elif isinstance(payload, dict):
        segments = (
            payload.get("transcript_segments")
            or payload.get("segments")
            or []
        )

        extra_text = payload.get("text", "")

        structured = payload.get("structured") or {}
        if isinstance(structured, dict):
            overview = structured.get("overview", "")
            if overview:
                extra_text = f"{overview} {extra_text}"
    else:
        return ""

    transcript_parts = []

    for segment in segments:
        if isinstance(segment, dict):
            segment_text = segment.get("text", "")
            if segment_text:
                transcript_parts.append(str(segment_text))

    combined = " ".join(
        [str(extra_text)] + transcript_parts
    ).strip()

    return combined


def save_omi_memory(uid: str, text: str, source: str):
    """Embed transcript text and save it in persistent Qdrant."""
    if not text.strip():
        return False

    ensure_omi_collection()

    vector = next(
        iter(embedding_model.embed([text]))
    ).tolist()

    qdrant.upsert(
        collection_name=OMI_COLLECTION,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "uid": uid,
                    "text": text,
                    "source": source,
                    "timestamp": time.time()
                }
            )
        ]
    )

    return True


@app.post("/omi/conversation")
def omi_conversation(
    uid: str,
    payload: dict = Body(...)
):
    """Receive a completed Omi conversation."""
    transcript = extract_omi_text(payload)

    if not transcript:
        return {
            "status": "ok",
            "saved": False,
            "message": "No transcript text found"
        }

    saved = save_omi_memory(
        uid=uid,
        text=transcript,
        source="conversation"
    )

    return {
        "status": "ok",
        "saved": saved,
        "source": "conversation"
    }


@app.post("/omi/realtime")
def omi_realtime(
    uid: str,
    payload: Any = Body(...),
    session_id: str = ""
):
    """Receive live transcript segments from Omi."""
    transcript = extract_omi_text(payload)

    if not transcript:
        return {
            "status": "ok",
            "saved": False,
            "message": "No transcript text found"
        }

    saved = save_omi_memory(
        uid=uid,
        text=transcript,
        source="realtime"
    )

    return {
        "status": "ok",
        "saved": saved,
        "source": "realtime",
        "session_id": session_id
    }

@app.get("/omi/memory-status")
def omi_memory_status():
    if qdrant is None:
        raise HTTPException(
            status_code=503,
            detail="Qdrant is not connected"
        )

    collection = "omi_memories"

    if not qdrant.collection_exists(collection):
        return {
            "collection_exists": False,
            "stored_memories": 0
        }

    result = qdrant.count(
        collection_name=collection,
        exact=True
    )

    return {
        "collection_exists": True,
        "stored_memories": result.count
    }
@app.get("/omi/memory-status")
def omi_memory_status():
    if qdrant is None:
        raise HTTPException(
            status_code=503,
            detail="Qdrant is not connected"
        )

    collection = "omi_memories"

    if not qdrant.collection_exists(collection):
        return {
            "collection_exists": False,
            "stored_memories": 0
        }

    result = qdrant.count(
        collection_name=collection,
        exact=True
    )

    return {
        "collection_exists": True,
        "stored_memories": result.count
    }
@app.post("/omi/search-memory")
def search_omi_memory(
    uid: str,
    query: str = Body(..., embed=True)
):
    if qdrant is None or embedding_model is None:
        raise HTTPException(
            status_code=503,
            detail="Qdrant or embedding model is unavailable"
        )

    collection = "omi_memories"

    if not qdrant.collection_exists(collection):
        return {"results": []}

    vector = next(
        iter(embedding_model.embed([query]))
    ).tolist()

    results = qdrant.query_points(
        collection_name=collection,
        query=vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="uid",
                    match=MatchValue(value=uid)
                )
            ]
        ),
        limit=5,
        with_payload=True
    ).points

    return {
        "query": query,
        "results": [
            {
                "text": point.payload.get("text", ""),
                "source": point.payload.get("source", ""),
                "score": point.score
            }
            for point in results
        ]
    }
@app.get("/omi/debug-memories")
def debug_omi_memories():
    if qdrant is None:
        raise HTTPException(
            status_code=503,
            detail="Qdrant is not connected"
        )

    if not qdrant.collection_exists("omi_memories"):
        return {"memories": []}

    result = qdrant.scroll(
        collection_name="omi_memories",
        limit=10,
        with_payload=True,
        with_vectors=False
    )

    return {
        "memories": [
            {
                "uid": point.payload.get("uid"),
                "text": point.payload.get("text"),
                "source": point.payload.get("source")
            }
            for point in result[0]
        ]
    }
