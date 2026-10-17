import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Body
from app.database import get_db_connection
from app.schemas import NoteUpdateSchema, GenerateAudioRequest
from app.services.audio_generator import generate_audio_lesson, DEFAULT_VOICES
from app.services.video_generator import generate_video_lesson

router = APIRouter(prefix="/api/lessons", tags=["Lessons"])

@router.get("/{lesson_id}")
def get_lesson(lesson_id: str, lang: str = "ro"):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    l_row = cursor.fetchone()
    if not l_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Lesson not found")

    lesson = dict(l_row)

    # Parse JSON fields
    for field in ["key_ideas", "practical_insights", "examples", "action_items", "transcript", "transcript_ro", "transcript_en"]:
        val = lesson.get(field)
        if val and isinstance(val, str):
            try:
                lesson[field] = json.loads(val)
            except Exception:
                lesson[field] = []
        elif not val:
            lesson[field] = []

    # Get course title
    cursor.execute("SELECT title, book_id FROM courses WHERE id = ?", (lesson["course_id"],))
    course = cursor.fetchone()
    course_title = course["title"] if course else "Course"

    # Ensure audio URLs and files exist without blocking
    if not lesson.get("audio_url_ro"):
        lesson["audio_url_ro"] = f"/media/audio/{lesson_id}_ro.mp3"
    if not lesson.get("audio_url_en"):
        lesson["audio_url_en"] = f"/media/audio/{lesson_id}_en.mp3"
    if not lesson.get("video_url"):
        lesson["video_url"] = f"/media/video/{lesson_id}.mp4"

    # Select active audio_url and transcript based on requested lang
    if lang == "en":
        lesson["active_audio_url"] = lesson.get("audio_url_en") or lesson.get("audio_url") or f"/media/audio/{lesson_id}_en.mp3"
        lesson["active_transcript"] = lesson.get("transcript_en") or lesson.get("transcript") or []
    else:
        lesson["active_audio_url"] = lesson.get("audio_url_ro") or lesson.get("audio_url") or f"/media/audio/{lesson_id}_ro.mp3"
        lesson["active_transcript"] = lesson.get("transcript_ro") or lesson.get("transcript") or []

    # Fallback to main audio_url if active is missing
    if not lesson.get("audio_url"):
        lesson["audio_url"] = lesson["active_audio_url"]

    # Find prev and next lesson in course
    cursor.execute("""
    SELECT id, title, order_index FROM lessons
    WHERE course_id = ?
    ORDER BY order_index ASC
    """, (lesson["course_id"],))
    all_lessons = [dict(r) for r in cursor.fetchall()]
    
    current_idx = next((i for i, item in enumerate(all_lessons) if item["id"] == lesson_id), -1)
    lesson["prev_lesson"] = all_lessons[current_idx - 1] if current_idx > 0 else None
    lesson["next_lesson"] = all_lessons[current_idx + 1] if current_idx < len(all_lessons) - 1 else None

    # Get notes
    cursor.execute("SELECT content FROM notes WHERE lesson_id = ?", (lesson_id,))
    note = cursor.fetchone()
    lesson["notes"] = note["content"] if note else ""

    conn.close()
    return lesson

@router.post("/{lesson_id}/language/{lang}")
def switch_lesson_language(lesson_id: str, lang: str):
    """
    Switches audio & transcript between 'ro' and 'en' for the specified lesson.
    Returns the audio URL and updated metadata.
    """
    if lang not in ["ro", "en"]:
        raise HTTPException(status_code=400, detail="Limba suportată este 'ro' sau 'en'.")
    return get_lesson(lesson_id=lesson_id, lang=lang)

@router.post("/{lesson_id}/complete")
def toggle_lesson_completion(lesson_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT completed FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Lesson not found")

    new_status = 0 if row["completed"] else 1
    cursor.execute("UPDATE lessons SET completed = ? WHERE id = ?", (new_status, lesson_id))
    conn.commit()
    conn.close()
    return {"lesson_id": lesson_id, "completed": bool(new_status)}

@router.post("/{lesson_id}/notes")
def save_lesson_notes(lesson_id: str, note_data: NoteUpdateSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_id FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Lesson not found")

    course_id = row["course_id"]
    cursor.execute("""
    INSERT INTO notes (id, course_id, lesson_id, content, updated_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(id) DO UPDATE SET content = excluded.content, updated_at = CURRENT_TIMESTAMP
    """, (f"note-{lesson_id}", course_id, lesson_id, note_data.content))
    conn.commit()
    conn.close()
    return {"status": "saved", "lesson_id": lesson_id}

@router.post("/{lesson_id}/generate-audio")
def regenerate_lesson_audio(lesson_id: str, req: Optional[GenerateAudioRequest] = Body(default=None)):
    """
    Synthesizes studio-grade neural voice in Romanian (or English) via edge-tts.
    Updates the lesson's audio URL, exact audio duration, and scene timestamp alignments.
    """
    req = req or GenerateAudioRequest()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    l_row = cursor.fetchone()
    if not l_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Lesson not found")

    lesson = dict(l_row)
    lang_code = "ro" if req.lang == "ro" else "en"

    def _parse(val):
        if val and isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return val or []

    key_ideas = _parse(lesson.get("key_ideas"))
    practical_insights = _parse(lesson.get("practical_insights"))
    examples = _parse(lesson.get("examples"))
    action_items = _parse(lesson.get("action_items"))

    voice_to_use = req.voice or (DEFAULT_VOICES["ro"] if lang_code == "ro" else DEFAULT_VOICES["en"])

    audio_url, duration_sec, scenes = generate_audio_lesson(
        lesson_id=lesson_id,
        title=lesson.get("title", ""),
        summary=lesson.get("short_summary", ""),
        long_explanation=lesson.get("long_explanation", ""),
        key_ideas=key_ideas,
        practical_insights=practical_insights,
        examples=examples,
        action_items=action_items,
        conclusion="Stăpâniți aceste fundamente pentru a acționa cu maximă eficiență." if lang_code == "ro" else "Master these principles to achieve immediate operational clarity.",
        custom_script=req.custom_script or "",
        lang=lang_code,
        voice=voice_to_use,
        rate=req.rate or "+0%",
        return_details=True
    )

    mins = max(1, int(round(duration_sec / 60)))
    duration_str = f"{mins} min{'s' if mins > 1 else ''}"
    scenes_json = json.dumps(scenes)

    if lang_code == "ro":
        cursor.execute("""
        UPDATE lessons 
        SET audio_url_ro = ?, transcript_ro = ?, duration = ?, audio_url = ?
        WHERE id = ?
        """, (audio_url, scenes_json, duration_str, audio_url, lesson_id))
    else:
        cursor.execute("""
        UPDATE lessons 
        SET audio_url_en = ?, transcript_en = ?
        WHERE id = ?
        """, (audio_url, scenes_json, lesson_id))

    conn.commit()
    conn.close()

    return get_lesson(lesson_id=lesson_id, lang=lang_code)

