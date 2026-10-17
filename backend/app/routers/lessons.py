import json
import re
from contextlib import closing
from fastapi import APIRouter, Body, Depends, HTTPException
from app.database import get_db_connection
from app.schemas import NoteUpdateSchema, GenerateAudioRequest
from app.security import check_course_access, optional_user, require_user
from app.routers.courses import user_lesson
from app.services.audio_generator import generate_audio_lesson, DEFAULT_VOICES
from app.generation_limits import generation_slot

router = APIRouter(prefix="/api/lessons", tags=["Lessons"])


def checked_lesson(conn,lesson_id,user,write=False):
    row = conn.execute("SELECT * FROM lessons WHERE id=?",(lesson_id,)).fetchone()
    if not row:
        raise HTTPException(404,"Lecția nu a fost găsită.")
    course = check_course_access(conn,row["course_id"],user,write)
    return dict(row),course


@router.get("/{lesson_id}")
def get_lesson(lesson_id: str,lang: str | None=None,user: dict | None=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        row,course = checked_lesson(conn,lesson_id,user)
        language = course.get("language") or "en"
        if lang is not None and lang != language:
            raise HTTPException(400,"Lecția folosește limba documentului sursă.")
        lesson = user_lesson(conn,row,user)
        lesson["language"] = language
        lesson["is_owner"] = bool(user and course["owner_id"] == user["id"])
        lesson["active_audio_url"] = lesson.get(f"audio_url_{language}") or lesson.get("audio_url") or None
        lesson["active_transcript"] = lesson.get(f"transcript_{language}") or lesson.get("transcript") or []
        all_lessons = [dict(item) for item in conn.execute("SELECT id,title,order_index FROM lessons WHERE course_id=? ORDER BY order_index,id",(lesson["course_id"],))]
        current = next(i for i,item in enumerate(all_lessons) if item["id"] == lesson_id)
        lesson["prev_lesson"] = all_lessons[current-1] if current else None
        lesson["next_lesson"] = all_lessons[current+1] if current+1 < len(all_lessons) else None
        note = conn.execute("SELECT content FROM notes WHERE lesson_id=? AND user_id=?",(lesson_id,user["id"])).fetchone() if user else None
        lesson["notes"] = note["content"] if note else ""
        return lesson


@router.post("/{lesson_id}/language/{lang}")
def switch_lesson_language(lesson_id: str,lang: str,user: dict | None=Depends(optional_user)):
    return get_lesson(lesson_id,lang,user)


@router.post("/{lesson_id}/complete")
def toggle_lesson_completion(lesson_id: str,user: dict=Depends(require_user)):
    with closing(get_db_connection()) as conn:
        checked_lesson(conn,lesson_id,user)
        row = conn.execute("SELECT completed FROM user_lesson_progress WHERE user_id=? AND lesson_id=?",(user["id"],lesson_id)).fetchone()
        completed = 0 if row and row["completed"] else 1
        conn.execute("""INSERT INTO user_lesson_progress(user_id,lesson_id,completed) VALUES(?,?,?)
            ON CONFLICT(user_id,lesson_id) DO UPDATE SET completed=excluded.completed,updated_at=CURRENT_TIMESTAMP""",(user["id"],lesson_id,completed))
        conn.commit()
    return {"lesson_id":lesson_id,"completed":bool(completed)}


@router.post("/{lesson_id}/notes")
def save_lesson_notes(lesson_id: str,note_data: NoteUpdateSchema,user: dict=Depends(require_user)):
    if len(note_data.content) > 50_000:
        raise HTTPException(422,"Notițele pot avea maximum 50.000 de caractere.")
    with closing(get_db_connection()) as conn:
        lesson,_ = checked_lesson(conn,lesson_id,user)
        conn.execute("""INSERT INTO notes(id,course_id,lesson_id,content,user_id) VALUES(?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET content=excluded.content,updated_at=CURRENT_TIMESTAMP""",
            (f"note-{user['id']}-{lesson_id}",lesson["course_id"],lesson_id,note_data.content,user["id"]))
        conn.commit()
    return {"status":"saved","lesson_id":lesson_id}


@router.post("/{lesson_id}/generate-audio")
def regenerate_lesson_audio(lesson_id: str,req: GenerateAudioRequest | None=Body(default=None),user: dict=Depends(require_user)):
    with closing(get_db_connection()) as conn:
        raw,course = checked_lesson(conn,lesson_id,user,write=True)
        lesson = user_lesson(conn,raw,user)
        language = course["language"] or "en"
        req = req or GenerateAudioRequest(lang=language)
        requested_language = req.lang if "lang" in req.model_fields_set else language
        if language not in ("ro","en") or requested_language != language:
            raise HTTPException(400,"Audio este disponibil pentru documente în română sau engleză, în limba sursei.")
        if req.custom_script and req.custom_script.strip():
            raise HTTPException(400,"Audio se generează din lecția documentului sursă.")
        voice = req.voice if "voice" in req.model_fields_set and req.voice else DEFAULT_VOICES[language]
        if not voice.startswith("ro-" if language == "ro" else "en-"):
            raise HTTPException(400,"Vocea trebuie să folosească limba documentului.")
        if not re.fullmatch(r"[+-]\d{1,2}%", req.rate or "+0%"):
            raise HTTPException(422,"Ritmul audio nu este valid.")
        with generation_slot(user["id"], "audio"):
            try:
                audio_url,duration,scenes = generate_audio_lesson(lesson_id=lesson_id,title=lesson["title"],
                    summary=lesson.get("short_summary") or "",long_explanation=lesson.get("long_explanation") or "",
                    key_ideas=lesson["key_ideas"],practical_insights=lesson["practical_insights"],examples=lesson["examples"],
                    action_items=lesson["action_items"],lang=language,voice=voice,rate=req.rate or "+0%",return_details=True)
            except Exception:
                raise HTTPException(503,"Serviciul audio nu este disponibil momentan. Lecția poate fi citită în continuare.") from None
        conn.execute(f"""UPDATE lessons SET audio_url=?,audio_url_{language}=?,transcript=?,transcript_{language}=?,duration=? WHERE id=?""",
            (audio_url,audio_url,json.dumps(scenes),json.dumps(scenes),f"{max(1,round(duration/60))} min",lesson_id))
        conn.commit()
    return get_lesson(lesson_id,language,user)
