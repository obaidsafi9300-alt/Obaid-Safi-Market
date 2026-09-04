from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sqlite3
import uuid
import shutil
from datetime import datetime

app = FastAPI(title="Obaid Safi Market Verification Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://obaidsafi9300-alt.github.io"
    ],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("verification_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

DB_FILE = "verification.db"


def create_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            country TEXT NOT NULL,
            id_type TEXT NOT NULL,
            id_front TEXT NOT NULL,
            id_back TEXT,
            selfie TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_database()


@app.get("/")
def home():
    return {
        "market": "Obaid Safi Market",
        "verification_server": "running"
    }


@app.post("/verify")
async def verify_identity(
    name: str = Form(...),
    email: str = Form(...),
    country: str = Form(...),
    idType: str = Form(...),
    consent: str = Form(...),
    idFront: UploadFile = File(...),
    selfie: UploadFile = File(...),
    idBack: UploadFile | None = File(None)
):
    if consent.lower() != "true":
        return {
            "success": False,
            "message": "Identity verification consent is required."
        }

    verification_id = str(uuid.uuid4())

    person_folder = UPLOAD_DIR / verification_id
    person_folder.mkdir(parents=True, exist_ok=True)

    front_path = person_folder / "id_front.jpg"
    selfie_path = person_folder / "selfie.jpg"

    with front_path.open("wb") as buffer:
        shutil.copyfileobj(idFront.file, buffer)

    with selfie_path.open("wb") as buffer:
        shutil.copyfileobj(selfie.file, buffer)

    back_path = None

    if idBack:
        back_path = person_folder / "id_back.jpg"

        with back_path.open("wb") as buffer:
            shutil.copyfileobj(idBack.file, buffer)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO verifications (
            id,
            name,
            email,
            country,
            id_type,
            id_front,
            id_back,
            selfie,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        verification_id,
        name,
        email,
        country,
        idType,
        str(front_path),
        str(back_path) if back_path else None,
        str(selfie_path),
        "Pending",
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "verification_id": verification_id,
        "status": "Pending",
        "message": "Verification submitted successfully."
    }
