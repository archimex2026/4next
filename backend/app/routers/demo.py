import os
from fastapi import APIRouter
from app.config import FFMPEG_EXE, GEMINI_API_KEY, DB_PATH
from app.database import init_db, get_db_connection
from app.services.demo_seeder import seed_demo_data

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])

@router.get("/status")
def get_system_status():
    ffmpeg_available = False
    try:
        import subprocess
        res = subprocess.run([FFMPEG_EXE, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ffmpeg_available = (res.returncode == 0)
    except Exception:
        pass

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as b_cnt FROM books")
    b_cnt = cursor.fetchone()["b_cnt"]
    cursor.execute("SELECT COUNT(*) as c_cnt FROM courses")
    c_cnt = cursor.fetchone()["c_cnt"]
    cursor.execute("SELECT COUNT(*) as l_cnt FROM lessons")
    l_cnt = cursor.fetchone()["l_cnt"]
    conn.close()

    return {
        "status": "online",
        "demo_ready": b_cnt > 0,
        "books_count": b_cnt,
        "courses_count": c_cnt,
        "lessons_count": l_cnt,
        "ffmpeg_ready": ffmpeg_available,
        "gemini_api_configured": bool(GEMINI_API_KEY),
        "db_location": str(DB_PATH)
    }

@router.post("/seed")
def trigger_seed():
    init_db()
    seed_demo_data(generate_media_assets=True)
    return {"status": "success", "message": "Demo data seeded with complete audio and video assets."}

@router.post("/reset")
def reset_library():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes")
    cursor.execute("DELETE FROM quizzes")
    cursor.execute("DELETE FROM flashcards")
    cursor.execute("DELETE FROM lessons")
    cursor.execute("DELETE FROM levels")
    cursor.execute("DELETE FROM courses")
    cursor.execute("DELETE FROM books")
    conn.commit()
    conn.close()
    
    seed_demo_data(generate_media_assets=True)
    return {"status": "reset", "message": "Reset complete. Ready for clean demonstration."}
