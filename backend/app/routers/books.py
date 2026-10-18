"""Private-by-default source ingestion with bounded extraction and grounded study output."""
import asyncio
import json
import uuid
from contextlib import closing
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.config import UPLOAD_DIR
from app.database import get_db_connection
from app.security import optional_user, require_user, check_book_access, can_read_book
from app.services.extractor import extract_document, ExtractionError, MAX_TEXT_CHARACTERS
from app.services.language import detect_document_language, resolve_language, LanguageAmbiguous, SUPPORTED_LANGUAGES
from app.services.ai_analyzer import analyze_book_with_gemini
from app.services.study_ai import TEXT, extract_keywords, fold
from app.generation_limits import consume_budget, generation_slot
from app.services.trash import move_book_to_trash
from app.services.segmented_generation import plan_segments, segment_pages, segment_target, save_plan, complete_segment, append_curriculum

router = APIRouter(prefix="/api/books", tags=["Books"])
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".epub", ".docx", ".txt", ".md"}


async def receive_source(file, text):
    """Only generated UUID names reach disk; all failure paths remove their temporary file."""
    if bool(text and text.strip()) == bool(file and file.filename):
        raise HTTPException(400, "Încarcă un fișier sau introdu text, folosind o singură sursă.")
    path = None
    try:
        if text and text.strip():
            if len(text) > MAX_TEXT_CHARACTERS:
                raise HTTPException(413, "Textul depășește limita de 1.000.000 de caractere.")
            extension, original_name = ".txt", "notițe.txt"
            path = UPLOAD_DIR / f"{uuid.uuid4().hex}{extension}"
            path.write_text(text.strip(), encoding="utf-8")
            size = path.stat().st_size
        else:
            original_name = Path(file.filename.replace("\\", "/")).name[:200]
            extension = Path(original_name).suffix.lower()
            if extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(400, "Format neacceptat. Folosește PDF, EPUB, DOCX, TXT sau MD.")
            path = UPLOAD_DIR / f"{uuid.uuid4().hex}{extension}"
            size = 0
            with path.open("wb") as stream:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(413, "Fișierul depășește limita de 15 MB.")
                    stream.write(chunk)
        document = await asyncio.to_thread(extract_document, path, extension)
        return path, original_name, extension, size, document
    except ExtractionError as exc:
        if path:
            path.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        if path:
            path.unlink(missing_ok=True)
        raise


def _language_error(exc):
    if isinstance(exc, LanguageAmbiguous):
        detection = exc.detection
        return HTTPException(422, detail={"code": "language_confirmation_required", "message": str(exc),
            "detected_language": detection["language"], "confidence": detection["confidence"],
            "candidates": detection["candidates"], "supported_languages": SUPPORTED_LANGUAGES})
    return HTTPException(422, str(exc))


@router.post("/inspect")
async def inspect_source(file: Optional[UploadFile] = File(None), text: Optional[str] = Form(None), user=Depends(require_user)):
    consume_budget(user["id"], "inspect")
    path, original_name, extension, size, document = await receive_source(file, text)
    try:
        detection = await asyncio.to_thread(detect_document_language, document["text"])
        return {"title": document["title"] or Path(original_name).stem, "file_name": original_name,
            "page_count": document["page_count"], "page_kind": document["page_kind"], "file_size": size,
            "detected_language": detection["language"], "language": detection["language"],
            "language_confidence": detection["confidence"], "language_confirmation_required": detection["ambiguous"],
            "language_supported": detection["language"] in SUPPORTED_LANGUAGES,
            "source_preview": [{"page": document['pages'][i]["page"], "text": document['pages'][i]["text"][:1000]}
                for i in sorted({0, len(document['pages'])//2, len(document['pages'])-1})],
            "segment_count": len(plan_segments(document['pages'], 20)),
            "keywords": await asyncio.to_thread(extract_keywords, document["text"]), "supported_languages": SUPPORTED_LANGUAGES}
    finally:
        path.unlink(missing_ok=True)


@router.post("/upload")
async def upload_book(file: Optional[UploadFile] = File(None), text: Optional[str] = Form(None),
    title: Optional[str] = Form(None), author: Optional[str] = Form(None), language: Optional[str] = Form(None),
    visibility: str = Form("private"), study_minutes: int = Form(20), depth: str = Form("standard"),
    focus_keywords: Optional[str] = Form(None), user=Depends(require_user)):
    if visibility not in {"private", "public"}:
        raise HTTPException(422, "Vizibilitatea trebuie să fie private sau public.")
    if not 5 <= study_minutes <= 120 or depth not in {"brief", "standard", "deep"}:
        raise HTTPException(422, "Alege între 5 și 120 de minute și profunzimea brief, standard sau deep.")
    if title and len(title.strip()) > 200 or author and len(author.strip()) > 150:
        raise HTTPException(422, "Titlul poate avea maximum 200 de caractere, iar autorul 150.")
    try:
        focus = json.loads(focus_keywords) if focus_keywords and focus_keywords.lstrip().startswith("[") else [v.strip() for v in (focus_keywords or "").split(",") if v.strip()]
        if not isinstance(focus, list) or len(focus) > 10 or any(not isinstance(term, str) or not 2 <= len(term) <= 80 for term in focus):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(422, "Alege maximum 10 cuvinte cheie (listă JSON sau separate prin virgulă).")

    path, original_name, extension, size, document = await receive_source(file, text)
    saved = False
    try:
        try:
            detection = await asyncio.to_thread(resolve_language, document["text"], language)
        except ValueError as exc:
            raise _language_error(exc) from exc
        if any(fold(term) not in fold(document["text"]) for term in focus):
            raise HTTPException(422, "Cuvintele cheie selectate trebuie să apară în material.")
        selected_language = detection["language"]
        labels_title = {"ro": "Notițele mele", "en": "My notes", "fr": "Mes notes", "de": "Meine Notizen", "es": "Mis apuntes", "it": "I miei appunti"}
        display_title = (title or "").strip() or document["title"] or (Path(original_name).stem if file else labels_title[selected_language])
        display_author = (author or "").strip()
        segments = plan_segments(document['pages'], study_minutes)
        first_pages = segment_pages(segments[0], document['pages']) if segments else document['pages']
        with generation_slot(user["id"], "upload"):
            curriculum = await analyze_book_with_gemini(display_title, display_author, '\n\n'.join(p['text'] for p in first_pages),
                language=selected_language, source_pages=first_pages,
                study_minutes=segments[0]['study_minutes'] if segments else study_minutes, depth=depth, focus_keywords=focus,
                **({'lesson_target': segment_target(segments[0])} if segments else {}))
        curriculum['keywords'] = extract_keywords(document['text'])
        book_id, course_id = f"book-{uuid.uuid4().hex}", f"course-{uuid.uuid4().hex}"
        levels = curriculum["levels"]
        lessons = [lesson for level in levels for lesson in level["lessons"]]
        palette = ["#365D4C", "#7B6249", "#5A6D83", "#85665F", "#687550"]
        with closing(get_db_connection()) as conn:
            with conn:
                conn.execute("""INSERT INTO books (id,title,author,file_path,file_name,file_type,file_size,cover_color,status,
                    page_count,language,owner_id,visibility,source_text,source_pages,keywords,focus_keywords,study_minutes,depth,generation_mode,summary)
                    VALUES (?,?,?,?,?,?,?,?,'ready',?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (book_id, display_title, display_author, str(path), original_name, extension.lstrip("."), size,
                     palette[int(book_id[-2:], 16) % len(palette)], document["page_count"], selected_language, user["id"], visibility,
                     document["text"], json.dumps(document["pages"], ensure_ascii=False), json.dumps(curriculum["keywords"], ensure_ascii=False),
                     json.dumps(focus, ensure_ascii=False), study_minutes, depth, curriculum["generation_mode"], curriculum["overview"]))
                conn.execute("""INSERT INTO courses (id,book_id,title,subtitle,overview,target_audience,estimated_duration,
                    level_count,lesson_count,quiz_count,flashcard_count,language) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (course_id, book_id, curriculum["title"], curriculum["subtitle"], curriculum["overview"], curriculum["target_audience"],
                     f'{study_minutes} {TEXT[selected_language]["minutes"]}', len(levels), len(lessons), len(curriculum["quizzes"]), len(curriculum["flashcards"]), selected_language))
                added = append_curriculum(conn, course_id, curriculum)
                if segments:
                    save_plan(conn, book_id, segments)
                    complete_segment(conn, book_id, 0, curriculum, added)
        saved = True
        return {"status": "ready", "book_id": book_id, "course_id": course_id, "title": display_title, "author": display_author,
            "language": selected_language, "detected_language": detection["language"], "language_confidence": detection["confidence"],
            "visibility": visibility, "study_minutes": study_minutes, "depth": depth, "keywords": curriculum["keywords"],
            "focus_keywords": focus,
            "generation_mode": curriculum["generation_mode"], "page_kind": document["page_kind"],
            "levels_count": len(levels), "lessons_count": len(lessons), "quizzes_count": len(curriculum["quizzes"]),
            "flashcards_count": len(curriculum["flashcards"])}
    finally:
        if not saved:
            path.unlink(missing_ok=True)


def _public_book(book):
    result = {key: value for key, value in book.items() if key not in {"file_path", "source_text", "source_pages"}}
    result["keywords"] = json.loads(result.get("keywords") or "[]")
    result["focus_keywords"] = json.loads(result.get("focus_keywords") or "[]")
    return result


@router.get("")
def list_books(user=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        rows = [dict(row) for row in conn.execute("SELECT * FROM books ORDER BY created_at DESC")]
        return [_public_book(book) for book in rows if can_read_book(conn, book, user)]


@router.get("/{book_id}")
def get_book(book_id: str, user=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        book = check_book_access(conn, book_id, user)
        course = conn.execute("SELECT id FROM courses WHERE book_id=?", (book_id,)).fetchone()
    return {**_public_book(book), "course_id": course["id"] if course else None}


@router.delete("/{book_id}")
def delete_book(book_id: str, user=Depends(require_user)):
    with closing(get_db_connection()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        book = check_book_access(conn, book_id, user, write=True)
        result = move_book_to_trash(conn,book)
        course = conn.execute("SELECT id FROM courses WHERE book_id=?",(book_id,)).fetchone()
    return {**result,"course_id":course["id"] if course else None}
