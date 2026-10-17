"""Render readiness uses only a bounded database query; it never calls an AI provider."""
import sqlite3
from contextlib import closing
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.database import get_db_connection

router = APIRouter(tags=["Health"])


@router.get("/api/health")
def health():
    try:
        with closing(get_db_connection()) as conn:
            conn.execute("PRAGMA busy_timeout=1000")
            if conn.execute("SELECT 1").fetchone()[0] != 1:
                raise sqlite3.DatabaseError()
    except (sqlite3.Error,OSError):
        return JSONResponse({"status":"unavailable","database":"unavailable"},status_code=503)
    return {"status":"ok","database":"ok"}
