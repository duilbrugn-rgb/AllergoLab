from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import json
import logging
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import bcrypt
import jwt
import requests
from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends, Header
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

from algorithm import aggregate

# --- Config ---
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@allergolab.it')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
CORS_ORIGINS = [o.strip() for o in os.environ.get('CORS_ORIGINS', '*').split(',') if o.strip()]
EMERGENT_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"

# Load allergen dataset
with open(ROOT_DIR / 'allergens.json', 'r', encoding='utf-8') as f:
    ALLERGENS = json.load(f)
ALLERGENS_BY_CODE = {a['code']: a for a in ALLERGENS}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("allergolab")

app = FastAPI(title="AllergoLab API")
api_router = APIRouter(prefix="/api")


# --- Helpers: password / jwt ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "type": "access",
               "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "type": "refresh",
               "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def set_auth_cookies(response: Response, access: str, refresh: str):
    response.set_cookie("access_token", access, httponly=True, secure=True,
                        samesite="none", max_age=12 * 3600, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=True,
                        samesite="none", max_age=7 * 24 * 3600, path="/")


def public_user(doc: dict) -> dict:
    return {
        "user_id": doc["user_id"],
        "email": doc["email"],
        "name": doc.get("name", ""),
        "first_name": doc.get("first_name", ""),
        "last_name": doc.get("last_name", ""),
        "role": doc.get("role", "user"),
        "auth_provider": doc.get("auth_provider", "password"),
        "picture": doc.get("picture", ""),
    }


async def get_current_user(request: Request) -> dict:
    # 1) JWT access token (cookie or Bearer)
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") == "access":
                user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
                if user:
                    return user
        except jwt.PyJWTError:
            pass

    # 2) Emergent Google session token (cookie or Bearer)
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at >= datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    return user

    raise HTTPException(status_code=401, detail="Non autenticato")


# --- Models ---
class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class PatientInfo(BaseModel):
    first_name: str = ""
    last_name: str = ""
    dob: str = ""


class ReportInput(BaseModel):
    patient: PatientInfo
    doctor_name: str
    allergen_codes: List[str]
    notes: str = ""
    letterhead: str = ""


class AggregateInput(BaseModel):
    codes: List[str]


# --- Auth endpoints ---
@api_router.post("/auth/register")
async def register(data: RegisterInput, response: Response):
    email = data.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email già registrata")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    full_name = f"{data.first_name.strip()} {data.last_name.strip()}".strip()
    doc = {
        "user_id": user_id,
        "email": email,
        "password_hash": hash_password(data.password),
        "first_name": data.first_name.strip(),
        "last_name": data.last_name.strip(),
        "name": full_name,
        "role": "user",
        "auth_provider": "password",
        "picture": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(doc)
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)
    return public_user(doc)


@api_router.post("/auth/login")
async def login(data: LoginInput, response: Response):
    email = data.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not user.get("password_hash") or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email o password non validi")
    access = create_access_token(user["user_id"], email)
    refresh = create_refresh_token(user["user_id"])
    set_auth_cookies(response, access, refresh)
    return public_user(user)


@api_router.post("/auth/logout")
async def logout(response: Response, request: Request):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}


@api_router.post("/auth/refresh")
async def refresh_token_endpoint(request: Request, response: Response):
    rt = request.cookies.get("refresh_token")
    if not rt:
        raise HTTPException(status_code=401, detail="Refresh token mancante")
    try:
        payload = jwt.decode(rt, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token non valido")
        user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        access = create_access_token(user["user_id"], user["email"])
        response.set_cookie("access_token", access, httponly=True, secure=True,
                            samesite="none", max_age=12 * 3600, path="/")
        return {"ok": True}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token non valido")


@api_router.post("/auth/google/session")
async def google_session(response: Response, x_session_id: str = Header(None)):
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Session ID mancante")
    try:
        r = requests.get(EMERGENT_SESSION_URL, headers={"X-Session-ID": x_session_id}, timeout=10)
    except Exception:
        raise HTTPException(status_code=502, detail="Errore contattando il servizio di autenticazione")
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Sessione Google non valida")
    data = r.json()
    email = data["email"].lower().strip()
    name = data.get("name", "") or email.split("@")[0]
    picture = data.get("picture", "")
    session_token = data["session_token"]

    user = await db.users.find_one({"email": email})
    if not user:
        parts = name.split(" ", 1)
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "user_id": user_id,
            "email": email,
            "password_hash": None,
            "first_name": parts[0],
            "last_name": parts[1] if len(parts) > 1 else "",
            "name": name,
            "role": "user",
            "auth_provider": "google",
            "picture": picture,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one(user)
    else:
        if picture and not user.get("picture"):
            await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"picture": picture}})

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {"$set": {"user_id": user["user_id"], "session_token": session_token,
                  "expires_at": expires_at.isoformat(),
                  "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    response.set_cookie("session_token", session_token, httponly=True, secure=True,
                        samesite="none", max_age=7 * 24 * 3600, path="/")
    return public_user(user)


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return public_user(user)


# --- Allergens ---
@api_router.get("/allergens")
async def get_allergens(user: dict = Depends(get_current_user)):
    return ALLERGENS


# --- Aggregation ---
@api_router.post("/aggregate")
async def aggregate_codes(data: AggregateInput, user: dict = Depends(get_current_user)):
    items = [ALLERGENS_BY_CODE[c] for c in data.codes if c in ALLERGENS_BY_CODE]
    return aggregate(items)


# --- Reports ---
@api_router.post("/reports")
async def create_report(data: ReportInput, user: dict = Depends(get_current_user)):
    items = [ALLERGENS_BY_CODE[c] for c in data.allergen_codes if c in ALLERGENS_BY_CODE]
    agg = aggregate(items)
    report_id = f"rep_{uuid.uuid4().hex[:12]}"
    doc = {
        "report_id": report_id,
        "user_id": user["user_id"],
        "patient": data.patient.model_dump(),
        "doctor_name": data.doctor_name,
        "notes": data.notes,
        "letterhead": data.letterhead,
        "allergen_codes": data.allergen_codes,
        "allergens": items,
        "aggregation": agg,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.reports.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.get("/reports")
async def list_reports(user: dict = Depends(get_current_user)):
    docs = await db.reports.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return docs


@api_router.get("/reports/{report_id}")
async def get_report(report_id: str, user: dict = Depends(get_current_user)):
    doc = await db.reports.find_one({"report_id": report_id, "user_id": user["user_id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Report non trovato")
    return doc


@api_router.delete("/reports/{report_id}")
async def delete_report(report_id: str, user: dict = Depends(get_current_user)):
    res = await db.reports.delete_one({"report_id": report_id, "user_id": user["user_id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report non trovato")
    return {"ok": True}


@api_router.get("/")
async def root():
    return {"message": "AllergoLab API", "allergens": len(ALLERGENS)}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ['*'] else ['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.user_sessions.create_index("session_token")
    await db.reports.create_index("user_id")
    # Seed admin/owner
    existing = await db.users.find_one({"email": ADMIN_EMAIL.lower()})
    if existing is None:
        await db.users.insert_one({
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": ADMIN_EMAIL.lower(),
            "password_hash": hash_password(ADMIN_PASSWORD),
            "first_name": "Duilio",
            "last_name": "Brugnoni",
            "name": "Duilio Brugnoni",
            "role": "admin",
            "auth_provider": "password",
            "picture": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Admin seeded: %s", ADMIN_EMAIL)
    elif existing.get("password_hash") and not verify_password(ADMIN_PASSWORD, existing["password_hash"]):
        await db.users.update_one({"email": ADMIN_EMAIL.lower()},
                                  {"$set": {"password_hash": hash_password(ADMIN_PASSWORD)}})


@app.on_event("shutdown")
async def shutdown():
    client.close()
