"""Source workspace: citations, personal highlights, grounded questions, and local PDF exports."""
import json
import time
import uuid
from collections import defaultdict, deque
from contextlib import closing
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from app.database import get_db_connection
from app.security import optional_user, require_user, check_course_access, can_read_book
from app.services.study_ai import answer_from_source, TEXT, extract_keywords, tokens
from app.services.pdf_export import render_study_pdf

router = APIRouter(prefix="/api/study", tags=["Study workspace"])
_chat_requests = defaultdict(deque)


def _source(conn, course_id, user):
    course = check_course_access(conn, course_id, user)
    book = dict(conn.execute("SELECT * FROM books WHERE id=?", (course["book_id"],)).fetchone())
    pages = json.loads(book.get("source_pages") or "[]")
    if not pages and book.get("source_text"):
        pages = [{"page": 1, "text": book["source_text"]}]
    return course, book, pages


@router.get("/{course_id}/source")
def get_source(course_id: str, user=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        course, book, pages = _source(conn, course_id, user)
    return {"title": book["title"], "language": book["language"], "pages": pages,
        "page_kind": "page" if book.get("file_type") == "pdf" else "section",
        "keywords": json.loads(book.get("keywords") or "[]"), "study_minutes": book.get("study_minutes", 20),
        "focus_keywords": json.loads(book.get("focus_keywords") or "[]"),
        "depth": book.get("depth", "standard"), "generation_mode": book.get("generation_mode", "legacy"),
        "source_available": bool(pages)}


class ChatInput(BaseModel):
    message: str = Field(min_length=3, max_length=2000)
    previous_question: str | None = Field(default=None, max_length=2000)


@router.post("/{course_id}/chat")
async def source_chat(course_id: str, payload: ChatInput, user=Depends(require_user)):
    with closing(get_db_connection()) as conn:
        course, book, pages = _source(conn, course_id, user)
    if not pages:
        raise HTTPException(409, "Acest material vechi nu are sursa salvată. Încarcă documentul pentru a pune întrebări ancorate în sursă.")
    if book["language"] not in TEXT:
        raise HTTPException(422, "Limba documentului nu este suportată de asistentul de studiu.")
    # ponytail: per-process account limit; use a shared rate limiter when deploying multiple workers.
    now, window = time.monotonic(), _chat_requests[user["id"]]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= 15:
        raise HTTPException(429, "Ai trimis multe întrebări. Revino peste un minut.")
    window.append(now)
    return await answer_from_source(payload.message.strip(), pages, book["language"], book["title"], payload.previous_question)


def _highlights_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS highlights (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL, course_id TEXT NOT NULL,
        page INTEGER NOT NULL, start_offset INTEGER NOT NULL, end_offset INTEGER NOT NULL,
        text TEXT NOT NULL, color TEXT NOT NULL DEFAULT 'yellow', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)""")


@router.get("/{course_id}/highlights")
def list_highlights(course_id: str, user=Depends(require_user)):
    with closing(get_db_connection()) as conn:
        check_course_access(conn, course_id, user)
        _highlights_table(conn)
        return [dict(row) for row in conn.execute("SELECT * FROM highlights WHERE course_id=? AND user_id=? ORDER BY page,start_offset", (course_id, user["id"]))]


class HighlightInput(BaseModel):
    page: int = Field(ge=1, le=500)
    start_offset: int = Field(ge=0, le=1_000_000)
    end_offset: int = Field(ge=1, le=1_000_000)
    text: str = Field(min_length=1, max_length=5000)
    color: str = "yellow"


@router.post("/{course_id}/highlights", status_code=201)
def add_highlight(course_id: str, payload: HighlightInput, user=Depends(require_user)):
    if payload.color not in {"yellow", "green", "blue", "pink"}:
        raise HTTPException(422, "Culoarea nu este acceptată.")
    with closing(get_db_connection()) as conn:
        _, _, pages = _source(conn, course_id, user)
        page = next((item for item in pages if item["page"] == payload.page), None)
        if not page or payload.end_offset <= payload.start_offset or payload.end_offset > len(page["text"]) or page["text"][payload.start_offset:payload.end_offset] != payload.text:
            raise HTTPException(422, "Selecția nu corespunde textului sursă. Selectează din nou fragmentul.")
        _highlights_table(conn)
        highlight_id = f"hl-{uuid.uuid4().hex}"
        with conn:
            conn.execute("INSERT INTO highlights (id,user_id,course_id,page,start_offset,end_offset,text,color) VALUES (?,?,?,?,?,?,?,?)",
                (highlight_id, user["id"], course_id, payload.page, payload.start_offset, payload.end_offset, payload.text, payload.color))
        return dict(conn.execute("SELECT * FROM highlights WHERE id=?", (highlight_id,)).fetchone())


@router.delete("/{course_id}/highlights/{highlight_id}")
def delete_highlight(course_id: str, highlight_id: str, user=Depends(require_user)):
    with closing(get_db_connection()) as conn:
        check_course_access(conn, course_id, user)
        _highlights_table(conn)
        with conn:
            removed = conn.execute("DELETE FROM highlights WHERE id=? AND user_id=? AND course_id=?", (highlight_id, user["id"], course_id)).rowcount
        if not removed:
            raise HTTPException(404, "Evidențierea nu a fost găsită.")
    return {"status": "deleted", "id": highlight_id}


@router.get("/{course_id}/suggestions")
def get_suggestions(course_id: str, concept: str = Query("", max_length=100), user=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        _, book, pages = _source(conn, course_id, user)
        keywords = json.loads(book.get("keywords") or "[]")
        labels = TEXT.get(book["language"])
        if labels is None:
            raise HTTPException(422, "Limba documentului nu este încă suportată pentru sugestii.")
        if concept and concept.lower() not in (book.get("source_text") or "").lower():
            raise HTTPException(422, "Alege un concept din material.")
        relevant_text = " ".join(page["text"] for page in pages if not concept or concept.lower() in page["text"].lower())
        related = [term for term in extract_keywords(relevant_text, 12) if term.lower() != concept.lower()][:5]
        source_tokens = tokens(" ".join(keywords))
        courses = []
        for row in conn.execute("""SELECT c.id,c.title,c.book_id,b.keywords,b.visibility,b.owner_id,
            b.id AS source_book_id,b.cover_color,b.language FROM courses c JOIN books b ON c.book_id=b.id
            WHERE c.id<>? AND b.deleted_at IS NULL""", (course_id,)):
            candidate = dict(row)
            if candidate["language"] != book["language"]:
                continue
            candidate_book = {"id": candidate["source_book_id"], "visibility": candidate["visibility"], "owner_id": candidate["owner_id"]}
            overlap = source_tokens & tokens(" ".join(json.loads(candidate["keywords"] or "[]")))
            if overlap and can_read_book(conn, candidate_book, user):
                courses.append({"id": candidate["id"], "title": candidate["title"], "cover_color": candidate["cover_color"], "shared_concepts": sorted(overlap)[:4]})
        query = " ".join(([concept] if concept else []) + (related[:2] or keywords[:2]))
        return {"concepts": [{"term": term, "query": term, "reason": labels["related"]} for term in related],
                "courses": courses[:5], "google_query": query, "google_url": "https://www.google.com/search?" + urlencode({"q": query})}


_PDF_LABELS = {
    "ro": ("Sursă", "Lecție", "Flashcard", "Test", "Răspuns", "Întrebări", "pagina", "secțiunea"),
    "en": ("Source", "Lesson", "Flashcard", "Quiz", "Answer", "Questions", "page", "section"),
    "fr": ("Source", "Leçon", "Fiche", "Quiz", "Réponse", "Questions", "page", "section"),
    "de": ("Quelle", "Lektion", "Lernkarte", "Test", "Antwort", "Fragen", "Seite", "Abschnitt"),
    "es": ("Fuente", "Lección", "Tarjeta", "Prueba", "Respuesta", "Preguntas", "página", "sección"),
    "it": ("Fonte", "Lezione", "Scheda", "Quiz", "Risposta", "Domande", "pagina", "sezione"),
}


@router.get("/{course_id}/pdf")
def export_pdf(course_id: str, kind: str = "all", user=Depends(optional_user)):
    if kind not in {"all", "source", "lessons", "flashcards", "quiz"}:
        raise HTTPException(422, "Tipul exportului nu este valid.")
    with closing(get_db_connection()) as conn:
        course, book, pages = _source(conn, course_id, user)
        labels = _PDF_LABELS.get(book["language"])
        if labels is None:
            raise HTTPException(422, "Limba documentului nu este suportată pentru export.")
        sections = []
        if kind in {"all", "source"}:
            if not pages:
                raise HTTPException(409, "Sursa nu a fost păstrată pentru acest material. Încarcă din nou documentul.")
            page_label = labels[6] if book.get("file_type") == "pdf" else labels[7]
            sections += [(f"{labels[0]} · {page_label} {page['page']}", page["text"]) for page in pages]
        if kind in {"all", "lessons"}:
            for lesson in conn.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY order_index", (course_id,)):
                content = lesson["long_explanation"] or lesson["short_summary"] or ""
                citations = json.loads(lesson["source_citations"] or "[]")
                if citations:
                    content += "\n\n" + "\n".join(f"[{citation['page']}] {citation['text']}" for citation in citations)
                sections.append((f"{labels[1]} · {lesson['title']}", content))
        if kind in {"all", "flashcards"}:
            sections += [(f"{labels[2]} · {index + 1}", f"{card['question']}\n\n{labels[4]}: {card['answer']}")
                         for index, card in enumerate(conn.execute("SELECT * FROM flashcards WHERE course_id=?", (course_id,)))]
        if kind in {"all", "quiz"}:
            answers = []
            for index, quiz in enumerate(conn.execute("SELECT * FROM quizzes WHERE course_id=?", (course_id,))):
                options = json.loads(quiz["options"])
                sections.append((f"{labels[3]} · {index + 1}", quiz["question"] + "\n" + "\n".join(f"{chr(65 + i)}. {option}" for i, option in enumerate(options))))
                answers.append(f"{index + 1}. {chr(65 + quiz['correct_index'])} · {quiz['explanation']}")
            if answers:
                sections.append((labels[4], "\n\n".join(answers)))
    try:
        payload = render_study_pdf(book["title"], book["language"], sections)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    return Response(payload, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="4next-{kind}-{course_id}.pdf"', "Cache-Control": "private, no-store"})
