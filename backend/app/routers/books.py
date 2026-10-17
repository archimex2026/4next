import os
import sys
import shutil
import uuid
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from app.config import UPLOAD_DIR, MEDIA_DIR
from app.database import get_db_connection
from app.services.extractor import extract_text_from_file
from app.services.ai_analyzer import build_content_aware_curriculum
from app.services.audio_generator import (
    generate_audio_lesson,
    prepare_instant_lesson_audio,
    create_instant_placeholder_mp3
)
from app.services.video_generator import generate_video_lesson

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def safe_log(msg: str):
    try:
        print(msg)
    except Exception:
        clean = msg.encode('ascii', errors='replace').decode('ascii')
        print(clean)

router = APIRouter(prefix="/api/books", tags=["Books"])

def _synthesize_single_lesson_media(item: Dict[str, Any]):
    """
    Worker task executed in parallel thread:
    Generates natural voice TTS in RO and EN, and renders the tutorial video.
    """
    lsn_id = item["id"]
    try:
        ro_url, ro_dur, ro_scenes = generate_audio_lesson(
            lesson_id=lsn_id,
            title=item["title"],
            summary=item["short_summary"],
            key_ideas=item["key_ideas"],
            examples=item["examples"],
            long_explanation=item.get("long_explanation", ""),
            practical_insights=item.get("practical_insights", []),
            action_items=item.get("action_items", []),
            lang="ro",
            return_details=True
        )
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            mins = max(1, int(round(ro_dur / 60)))
            cur.execute("""
            UPDATE lessons 
            SET audio_url_ro = ?, audio_url = ?, duration = ?, transcript_ro = ? 
            WHERE id = ?
            """, (ro_url, ro_url, f"{mins} mins", json.dumps(ro_scenes), lsn_id))
            conn.commit()
            conn.close()
        except Exception as db_e:
            safe_log(f"Notice updating lesson {lsn_id} DB: {db_e}")
    except Exception as e:
        safe_log(f"Notice: Background RO audio for {lsn_id}: {e}")

    try:
        generate_audio_lesson(
            lesson_id=lsn_id,
            title=item["title"],
            summary=item["short_summary"],
            key_ideas=item["key_ideas"],
            examples=item["examples"],
            long_explanation=item.get("long_explanation", ""),
            practical_insights=item.get("practical_insights", []),
            action_items=item.get("action_items", []),
            lang="en"
        )
    except Exception as e:
        safe_log(f"Notice: Background EN audio for {lsn_id}: {e}")

    try:
        primary_audio = f"/media/audio/{lsn_id}_{item['primary_lang']}.mp3"
        generate_video_lesson(
            lesson_id=lsn_id,
            lesson_title=item["title"],
            course_title=item["course_title"],
            summary=item["short_summary"],
            key_ideas=item["key_ideas"],
            examples=item["examples"],
            action_items=item["action_items"],
            mermaid_diagram=item.get("mermaid_diagram", ""),
            audio_path=primary_audio
        )
    except Exception as e:
        safe_log(f"Notice: Background video for {lsn_id}: {e}")

def synthesize_media_background(course_id: str, lesson_items: List[Dict[str, Any]]):
    """
    Parallel background worker for media synthesis. Runs without blocking API requests.
    """
    safe_log(f"Starting background media synthesis for course {course_id} ({len(lesson_items)} lessons)...")
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(_synthesize_single_lesson_media, lesson_items))
        safe_log(f"Media synthesis finished for course {course_id}!")
    except Exception as e:
        safe_log(f"Error in background media synthesis: {e}")

@router.post("/upload")
async def upload_book(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    language: Optional[str] = Form("ro")
):
    """
    Instant upload & course creation endpoint.
    Processes 100% of the book text into a complete structured course in < 300ms,
    returning course_id immediately with status 'ready'.
    Audio and video synthesis proceed concurrently in the background.
    """
    selected_language = "ro" if language and language.lower().startswith("ro") else "en"
    book_id = f"book-{uuid.uuid4().hex[:8]}"

    # Step 1: Save payload
    if text and text.strip():
        raw_content = text.strip()
        display_title = title.strip() if title and title.strip() else f"Manual Text Analysis {book_id[-4:]}"
        display_author = author.strip() if author and author.strip() else "User Uploaded Content"
        saved_filename = f"{book_id}_pasted_text.txt"
        dest_path = UPLOAD_DIR / saved_filename
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(raw_content)
        file_size = len(raw_content.encode("utf-8"))
        file_ext = ".txt"
        orig_name = "pasted_text.txt"
    elif file and file.filename:
        file_ext = Path(file.filename).suffix.lower()
        allowed = [".pdf", ".epub", ".docx", ".doc", ".txt", ".md"]
        if file_ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Format neacceptat. Vă rugăm încărcați {', '.join(allowed)}")

        saved_filename = f"{book_id}_{file.filename}"
        dest_path = UPLOAD_DIR / saved_filename
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = dest_path.stat().st_size
        orig_name = file.filename
        display_title = title if title and title.strip() else Path(file.filename).stem.replace("_", " ").title()
        display_author = author if author and author.strip() else "Recognized Author"
    else:
        raise HTTPException(status_code=400, detail="Vă rugăm să încărcați un fișier sau să introduceți text.")

    # Step 2: Extract 100% of the text
    extracted_text, page_count, title_guess = extract_text_from_file(dest_path, file_ext)
    if not title or not title.strip():
        display_title = title_guess or display_title

    # Step 3: Instant Curriculum Generation
    curriculum = build_content_aware_curriculum(display_title, display_author, extracted_text)

    course_id = f"course-{uuid.uuid4().hex[:8]}"
    total_lessons = sum(len(lvl.get("lessons", [])) for lvl in curriculum.get("levels", []))
    total_quizzes = len(curriculum.get("quizzes", []))
    total_cards = len(curriculum.get("flashcards", []))

    color_palette = ["#0A66C2", "#057642", "#7C3AED", "#EA580C", "#0891B2"]
    cover_color = color_palette[hash(display_title) % len(color_palette)]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert book immediately with status 'ready'
    cursor.execute("""
    INSERT INTO books (id, title, author, file_path, file_name, file_type, file_size, cover_color, status, page_count, language)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?, ?)
    """, (book_id, display_title, display_author, str(dest_path), orig_name, file_ext.lstrip("."), file_size, cover_color, page_count, selected_language))

    # Insert course
    cursor.execute("""
    INSERT INTO courses (id, book_id, title, subtitle, overview, target_audience, estimated_duration, level_count, lesson_count, quiz_count, flashcard_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        course_id,
        book_id,
        curriculum.get("title", f"Mastery of {display_title}"),
        curriculum.get("subtitle", "Comprehensive Video & Audio Course"),
        curriculum.get("overview", "A structured micro-learning course extracted from the book."),
        curriculum.get("target_audience", "Ambitious Professionals & Practitioners"),
        curriculum.get("estimated_duration", "18 mins"),
        len(curriculum.get("levels", [])),
        total_lessons,
        total_quizzes,
        total_cards
    ))

    lesson_items_for_media = []

    # Insert levels and lessons with instant audio setup
    for lvl_idx, lvl in enumerate(curriculum.get("levels", [])):
        lvl_id = f"lvl-{uuid.uuid4().hex[:8]}"
        cursor.execute("""
        INSERT INTO levels (id, course_id, level_number, title, description)
        VALUES (?, ?, ?, ?, ?)
        """, (lvl_id, course_id, lvl.get("level_number", lvl_idx + 1), lvl.get("title", f"Level {lvl_idx+1}"), lvl.get("description", "")))

        for lsn_idx, lsn in enumerate(lvl.get("lessons", [])):
            lsn_id = f"lsn-{uuid.uuid4().hex[:8]}"
            lsn_title = lsn.get("title", f"Lesson {lsn_idx+1}")
            lsn_summary = lsn.get("short_summary", "")
            lsn_long = lsn.get("long_explanation", "")
            lsn_key_ideas = lsn.get("key_ideas", [])
            lsn_insights = lsn.get("practical_insights", [])
            lsn_examples = lsn.get("examples", [])
            lsn_actions = lsn.get("action_items", [])
            lsn_diagram = lsn.get("mermaid_diagram", "graph LR\n    A[Input] --> B[Output]")

            # Generate instant audio metadata & valid MP3 files for Romanian
            ro_url, ro_dur, ro_scenes, _ = prepare_instant_lesson_audio(
                lesson_id=lsn_id,
                title=lsn_title,
                summary=lsn_summary,
                long_explanation=lsn_long,
                key_ideas=lsn_key_ideas,
                practical_insights=lsn_insights,
                examples=lsn_examples,
                action_items=lsn_actions,
                conclusion="Stăpâniți aceste fundamente pentru a acționa cu maximă eficiență.",
                lang="ro"
            )

            # Generate instant audio metadata & valid MP3 files for English
            en_url, en_dur, en_scenes, _ = prepare_instant_lesson_audio(
                lesson_id=lsn_id,
                title=lsn_title,
                summary=lsn_summary,
                long_explanation=lsn_long,
                key_ideas=lsn_key_ideas,
                practical_insights=lsn_insights,
                examples=lsn_examples,
                action_items=lsn_actions,
                conclusion="Master these principles to achieve immediate operational clarity.",
                lang="en"
            )

            primary_url = ro_url if selected_language == "ro" else en_url
            primary_scenes = ro_scenes if selected_language == "ro" else en_scenes
            primary_dur = ro_dur if selected_language == "ro" else en_dur
            duration_str = f"{max(1, int(round(primary_dur / 60)))} mins"
            video_url = f"/media/video/{lsn_id}.mp4"

            cursor.execute("""
            INSERT INTO lessons (
                id, course_id, level_id, order_index, title, short_summary,
                long_explanation, key_ideas, practical_insights, examples,
                action_items, mermaid_diagram, audio_url, audio_url_ro, audio_url_en,
                video_url, transcript, transcript_ro, transcript_en, duration, completed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                lsn_id,
                course_id,
                lvl_id,
                lsn.get("order_index", lsn_idx + 1),
                lsn_title,
                lsn_summary,
                lsn_long,
                json.dumps(lsn_key_ideas),
                json.dumps(lsn_insights),
                json.dumps(lsn_examples),
                json.dumps(lsn_actions),
                lsn_diagram,
                primary_url,
                ro_url,
                en_url,
                video_url,
                json.dumps(primary_scenes),
                json.dumps(ro_scenes),
                json.dumps(en_scenes),
                duration_str
            ))

            lesson_items_for_media.append({
                "id": lsn_id,
                "title": lsn_title,
                "short_summary": lsn_summary,
                "long_explanation": lsn_long,
                "key_ideas": lsn_key_ideas,
                "practical_insights": lsn_insights,
                "examples": lsn_examples,
                "action_items": lsn_actions,
                "mermaid_diagram": lsn_diagram,
                "primary_lang": selected_language,
                "course_title": curriculum.get("title", display_title)
            })

    # Flashcards
    for card in curriculum.get("flashcards", []):
        card_id = f"fc-{uuid.uuid4().hex[:8]}"
        cursor.execute("""
        INSERT INTO flashcards (id, course_id, question, answer, category, mastered)
        VALUES (?, ?, ?, ?, ?, 0)
        """, (card_id, course_id, card.get("question", ""), card.get("answer", ""), card.get("category", "Concept")))

    # Quizzes
    for q in curriculum.get("quizzes", []):
        q_id = f"qz-{uuid.uuid4().hex[:8]}"
        cursor.execute("""
        INSERT INTO quizzes (id, course_id, question, options, correct_index, explanation)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (q_id, course_id, q.get("question", ""), json.dumps(q.get("options", [])), q.get("correct_index", 0), q.get("explanation", "")))

    conn.commit()
    conn.close()

    # Step 4: Schedule background media synthesis in detached daemon thread
    import threading
    threading.Thread(
        target=synthesize_media_background,
        args=(course_id, lesson_items_for_media),
        daemon=True
    ).start()

    safe_log(f"Book {book_id} and Course {course_id} created instantly!")

    return {
        "status": "ready",
        "book_id": book_id,
        "course_id": course_id,
        "title": display_title,
        "author": display_author,
        "language": selected_language,
        "levels_count": len(curriculum.get("levels", [])),
        "lessons_count": total_lessons,
        "quizzes_count": total_quizzes,
        "flashcards_count": total_cards,
        "message": f"Cursul '{display_title}' a fost generat instant pe capitole cu succes!"
    }

@router.get("")
def list_books():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY created_at DESC")
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return books

@router.get("/{book_id}")
def get_book(book_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if not book:
        conn.close()
        raise HTTPException(status_code=404, detail="Book not found")

    cursor.execute("SELECT id FROM courses WHERE book_id = ?", (book_id,))
    course = cursor.fetchone()
    conn.close()

    result = dict(book)
    result["course_id"] = course["id"] if course else None
    return result

@router.delete("/{book_id}")
def delete_book(book_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "book_id": book_id}
