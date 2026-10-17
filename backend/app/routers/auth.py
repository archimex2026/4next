import re
import secrets
import sqlite3
import time
import uuid
from contextlib import closing
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from app.config import COOKIE_SECURE, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from app.database import get_db_connection
from app.security import USER_FIELDS, hash_password, optional_user, require_user, token_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["Accounts"])


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Introdu o adresă de e-mail validă.")
        return value


class Register(Login):
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=256)
    accept_terms: bool

    @field_validator("name")
    @classmethod
    def valid_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Introdu numele tău.")
        return value

    @field_validator("accept_terms")
    @classmethod
    def accepted_terms(cls, value):
        if not value:
            raise ValueError("Este necesară acceptarea termenilor.")
        return value


class Profile(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    study_minutes: int | None = Field(default=None, ge=5, le=120)
    depth: str | None = Field(default=None, pattern="^(brief|standard|deep)$")
    exam_goal: str | None = Field(default=None, max_length=200)


def throttle(conn, request: Request, email: str, action: str):
    now = int(time.time())
    # SQLite keeps this limit effective across workers; deploy behind a proxy that supplies real client IPs.
    keys = [(f"{action}:ip:{request.client.host if request.client else 'unknown'}", 30),
            (f"{action}:email:{email}", 8)]
    conn.execute("DELETE FROM auth_attempts WHERE window_start < ?", (now - 900,))
    for raw_key, limit in keys:
        key = token_hash(raw_key)
        row = conn.execute("SELECT attempts FROM auth_attempts WHERE key=?", (key,)).fetchone()
        if row and row["attempts"] >= limit:
            conn.commit()
            raise HTTPException(429, "Prea multe încercări. Revino peste 15 minute.", headers={"Retry-After":"900"})
        conn.execute("""INSERT INTO auth_attempts(key,attempts,window_start) VALUES(?,1,?)
            ON CONFLICT(key) DO UPDATE SET attempts=attempts+1""", (key,now))
    conn.commit()


def start_session(conn, user_id: str, request: Request, response: Response):
    old_token = request.cookies.get(SESSION_COOKIE_NAME)
    if old_token:
        conn.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(old_token),))
    token = secrets.token_urlsafe(32)
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (int(time.time()),))
    conn.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)",
        (token_hash(token),user_id,int(time.time())+SESSION_MAX_AGE))
    conn.commit()
    response.set_cookie(SESSION_COOKIE_NAME, token, max_age=SESSION_MAX_AGE,
        httponly=True, secure=COOKIE_SECURE, samesite="lax", path="/")


@router.post("/register", status_code=201)
def register(data: Register, request: Request, response: Response):
    with closing(get_db_connection()) as conn:
        throttle(conn, request, data.email, "register")
        user_id = "usr-" + uuid.uuid4().hex
        password = hash_password(data.password)
        try:
            conn.execute("""INSERT INTO users(id,name,email,password_hash,terms_accepted_at)
                VALUES(?,?,?,?,CURRENT_TIMESTAMP)""", (user_id,data.name,data.email,password))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409,"Adresa de e-mail are deja un cont.") from None
        start_session(conn,user_id,request,response)
        return {"user":dict(conn.execute(f"SELECT {USER_FIELDS} FROM users WHERE id=?",(user_id,)).fetchone())}


@router.post("/login")
def login(data: Login, request: Request, response: Response):
    with closing(get_db_connection()) as conn:
        throttle(conn,request,data.email,"login")
        row = conn.execute("SELECT * FROM users WHERE email=?",(data.email,)).fetchone()
        # Equal-cost check also for unknown addresses.
        encoded = row["password_hash"] if row else "pbkdf2_sha256$600000$00000000000000000000000000000000$" + "0"*64
        if not verify_password(data.password,encoded) or not row:
            raise HTTPException(401,"E-mailul sau parola nu sunt corecte.")
        start_session(conn,row["id"],request,response)
        return {"user":{field.strip():row[field.strip()] for field in USER_FIELDS.split(",")}}


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        with closing(get_db_connection()) as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash=?",(token_hash(token),))
            conn.commit()
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", secure=COOKIE_SECURE, httponly=True, samesite="lax")
    return {"status":"logged_out"}


@router.get("/me")
def me(response: Response, user: dict | None = Depends(optional_user)):
    response.headers["Cache-Control"] = "no-store"
    return {"user":user}


@router.patch("/profile")
def update_profile(data: Profile, user: dict = Depends(require_user)):
    values = data.model_dump(exclude_none=True)
    for field in ("name","exam_goal"):
        if field in values:
            values[field] = values[field].strip()
    if "name" in values and not values["name"]:
        raise HTTPException(422,"Numele nu poate fi gol.")
    with closing(get_db_connection()) as conn:
        if values:
            assignments = ", ".join(f"{field}=?" for field in values)
            conn.execute(f"UPDATE users SET {assignments} WHERE id=?",(*values.values(),user["id"]))
            conn.commit()
        return {"user":dict(conn.execute(f"SELECT {USER_FIELDS} FROM users WHERE id=?",(user["id"],)).fetchone())}
