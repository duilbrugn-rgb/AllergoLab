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
import hmac
import requests
from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends, Header, BackgroundTasks
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
WEBHOOK_CRON_SECRET = os.environ.get('WEBHOOK_CRON_SECRET', '')
REPORT_RETENTION_DAYS = 10

# Seed source for the allergen dataset (loaded into MongoDB on startup)
with open(ROOT_DIR / 'allergens.json', 'r', encoding='utf-8') as f:
    SEED_ALLERGENS = json.load(f)

ALLERGEN_TYPES = ["Alimenti", "Inalanti", "Farmaci", "Veleni", "Allergeni molecolari"]


async def fetch_allergens_by_codes(codes):
    docs = await db.allergens.find({"code": {"$in": codes}}, {"_id": 0}).to_list(2000)
    by_code = {d["code"]: d for d in docs}
    return [by_code[c] for c in codes if c in by_code]


async def log_allergen_change(action: str, allergen: dict, user: dict, details: str = ""):
    """Traccia chi/quando ha creato, modificato o eliminato un allergene."""
    await db.allergen_audit.insert_one({
        "action": action,  # create | update | delete
        "allergen_code": allergen.get("code"),
        "allergen_name": allergen.get("name"),
        "allergen_type": allergen.get("type"),
        "changed_by_id": user.get("user_id"),
        "changed_by_name": user.get("name") or user.get("email"),
        "changed_by_email": user.get("email"),
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

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


def _bearer_token(request: Request):
    auth_header = request.headers.get("Authorization", "")
    return auth_header[7:] if auth_header.startswith("Bearer ") else None


async def _user_from_jwt(token):
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    return await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})


def _session_active(session) -> bool:
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at >= datetime.now(timezone.utc)


async def _user_from_session(token):
    if not token:
        return None
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session or not _session_active(session):
        return None
    return await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})


async def get_current_user(request: Request) -> dict:
    # 1) JWT access token (cookie o Bearer)
    user = await _user_from_jwt(request.cookies.get("access_token") or _bearer_token(request))
    if user:
        return user
    # 2) Token di sessione Google gestito da Emergent (cookie o Bearer)
    user = await _user_from_session(request.cookies.get("session_token") or _bearer_token(request))
    if user:
        return user
    raise HTTPException(status_code=401, detail="Non autenticato")


async def get_admin_user(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accesso riservato agli amministratori")
    return user


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


class AllergenInput(BaseModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: str
    siss_code: str = Field(min_length=1)
    siss_description: str = ""


class RoleUpdate(BaseModel):
    role: str


class ProfileInput(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    allergen_codes: List[str]


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
    return await db.allergens.find({}, {"_id": 0}).sort("code", 1).to_list(2000)


# --- Aggregation ---
@api_router.post("/aggregate")
async def aggregate_codes(data: AggregateInput, user: dict = Depends(get_current_user)):
    items = await fetch_allergens_by_codes(data.codes)
    return aggregate(items)


# --- Reports ---
@api_router.post("/reports")
async def create_report(data: ReportInput, user: dict = Depends(get_current_user)):
    items = await fetch_allergens_by_codes(data.allergen_codes)
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


# --- Admin: gestione catalogo allergeni (solo amministratori) ---
@api_router.get("/admin/allergens")
async def admin_list_allergens(user: dict = Depends(get_admin_user)):
    return await db.allergens.find({}, {"_id": 0}).sort("code", 1).to_list(2000)


@api_router.post("/admin/allergens")
async def admin_create_allergen(data: AllergenInput, user: dict = Depends(get_admin_user)):
    if data.type not in ALLERGEN_TYPES:
        raise HTTPException(status_code=400, detail="Tipologia non valida")
    code = data.code.strip()
    if await db.allergens.find_one({"code": code}):
        raise HTTPException(status_code=400, detail="Codice già esistente")
    doc = data.model_dump()
    doc["code"] = code
    await db.allergens.insert_one(dict(doc))
    await log_allergen_change("create", doc, user, "Nuovo allergene aggiunto")
    return doc


@api_router.put("/admin/allergens/{code}")
async def admin_update_allergen(code: str, data: AllergenInput, user: dict = Depends(get_admin_user)):
    if data.type not in ALLERGEN_TYPES:
        raise HTTPException(status_code=400, detail="Tipologia non valida")
    existing = await db.allergens.find_one({"code": code}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Allergene non trovato")
    new_code = data.code.strip()
    if new_code != code and await db.allergens.find_one({"code": new_code}):
        raise HTTPException(status_code=400, detail="Il nuovo codice è già in uso")
    doc = data.model_dump()
    doc["code"] = new_code
    await db.allergens.update_one({"code": code}, {"$set": doc})
    changes = [f"{f}: '{existing.get(f)}' → '{doc.get(f)}'"
               for f in ("code", "name", "type", "siss_code", "siss_description")
               if existing.get(f) != doc.get(f)]
    await log_allergen_change("update", doc, user,
                              "; ".join(changes) if changes else "Nessuna modifica di campo")
    return doc


@api_router.delete("/admin/allergens/{code}")
async def admin_delete_allergen(code: str, user: dict = Depends(get_admin_user)):
    existing = await db.allergens.find_one({"code": code}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Allergene non trovato")
    await db.allergens.delete_one({"code": code})
    await log_allergen_change("delete", existing, user, "Allergene eliminato")
    return {"ok": True}


# --- Admin: registro modifiche (audit) ---
@api_router.get("/admin/audit")
async def admin_audit(user: dict = Depends(get_admin_user)):
    return await db.allergen_audit.find({}, {"_id": 0}).sort("timestamp", -1).to_list(300)


# --- Admin: gestione utenti e ruoli ---
@api_router.get("/admin/users")
async def admin_list_users(user: dict = Depends(get_admin_user)):
    docs = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", 1).to_list(1000)
    return [{
        "user_id": d["user_id"],
        "email": d["email"],
        "name": d.get("name", ""),
        "role": d.get("role", "user"),
        "auth_provider": d.get("auth_provider", "password"),
        "created_at": d.get("created_at"),
    } for d in docs]


@api_router.put("/admin/users/{user_id}/role")
async def admin_update_role(user_id: str, data: RoleUpdate, user: dict = Depends(get_admin_user)):
    if data.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Ruolo non valido")
    if user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Non puoi modificare il tuo stesso ruolo")
    target = await db.users.find_one({"user_id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    await db.users.update_one({"user_id": user_id}, {"$set": {"role": data.role}})
    target["role"] = data.role
    return public_user(target)


# --- Profili di allergeni (bundle non modificabili dall'utente) ---
@api_router.get("/profiles")
async def list_profiles(user: dict = Depends(get_current_user)):
    return await db.profiles.find({}, {"_id": 0}).sort("name", 1).to_list(500)


@api_router.post("/admin/profiles")
async def admin_create_profile(data: ProfileInput, user: dict = Depends(get_admin_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "profile_id": f"prof_{uuid.uuid4().hex[:12]}",
        "name": data.name.strip(),
        "description": data.description.strip(),
        "allergen_codes": data.allergen_codes,
        "created_by": user.get("name") or user.get("email"),
        "created_at": now,
        "updated_at": now,
    }
    await db.profiles.insert_one(dict(doc))
    return doc


@api_router.put("/admin/profiles/{profile_id}")
async def admin_update_profile(profile_id: str, data: ProfileInput, user: dict = Depends(get_admin_user)):
    if not await db.profiles.find_one({"profile_id": profile_id}):
        raise HTTPException(status_code=404, detail="Profilo non trovato")
    await db.profiles.update_one({"profile_id": profile_id}, {"$set": {
        "name": data.name.strip(),
        "description": data.description.strip(),
        "allergen_codes": data.allergen_codes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }})
    return await db.profiles.find_one({"profile_id": profile_id}, {"_id": 0})


@api_router.delete("/admin/profiles/{profile_id}")
async def admin_delete_profile(profile_id: str, user: dict = Depends(get_admin_user)):
    res = await db.profiles.delete_one({"profile_id": profile_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profilo non trovato")
    return {"ok": True}


# --- Cron: cancellazione report in archivio piu' vecchi di 10 giorni ---
async def _purge_old_reports():
    cutoff = (datetime.now(timezone.utc) - timedelta(days=REPORT_RETENTION_DAYS)).isoformat()
    res = await db.reports.delete_many({"created_at": {"$lt": cutoff}})
    logger.info("Cron purge: eliminati %d report piu' vecchi di %d giorni",
                res.deleted_count, REPORT_RETENTION_DAYS)


@api_router.post("/cron/purge-old-reports")
async def cron_purge_old_reports(request: Request, background_tasks: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    if not WEBHOOK_CRON_SECRET or not hmac.compare_digest(token, WEBHOOK_CRON_SECRET):
        raise HTTPException(status_code=401, detail="Non autorizzato")
    background_tasks.add_task(_purge_old_reports)
    return {"accepted": True}


@api_router.get("/")
async def root():
    count = await db.allergens.count_documents({})
    return {"message": "AllergoLab API", "allergens": count}


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
    await db.allergens.create_index("code", unique=True)
    if await db.allergens.count_documents({}) == 0:
        await db.allergens.insert_many([dict(a) for a in SEED_ALLERGENS])
        logger.info("Seeded %d allergens", len(SEED_ALLERGENS))
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
