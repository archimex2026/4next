import shutil
from contextlib import closing
from fastapi import APIRouter, HTTPException
from app.config import FFMPEG_EXE, GEMINI_API_KEY
from app.database import get_db_connection

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])


@router.get("/status")
def get_system_status():
    with closing(get_db_connection()) as conn:
        row = conn.execute("""SELECT
            (SELECT COUNT(*) FROM books WHERE visibility='public') books_count,
            (SELECT COUNT(*) FROM courses c JOIN books b ON b.id=c.book_id WHERE b.visibility='public') courses_count,
            (SELECT COUNT(*) FROM lessons l JOIN courses c ON c.id=l.course_id JOIN books b ON b.id=c.book_id WHERE b.visibility='public') lessons_count""").fetchone()
    return {"status":"online","demo_ready":row["books_count"] > 0,**dict(row),
        "ffmpeg_ready":bool(shutil.which(FFMPEG_EXE)),"gemini_api_configured":bool(GEMINI_API_KEY)}


@router.post("/seed")
@router.post("/reset")
def disabled_demo_mutation():
    raise HTTPException(403,"Biblioteca de demonstrație se pregătește numai la pornirea serverului. Materialele utilizatorilor nu se resetează.")
