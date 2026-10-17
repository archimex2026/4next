import json
from contextlib import closing
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from app.config import MEDIA_DIR
from app.database import get_db_connection
from app.security import check_course_access, optional_user
from app.routers.lessons import checked_lesson

router = APIRouter(prefix="/api/export", tags=["Export"])


def attachment(title,extension):
    return {"Content-Disposition":f"attachment; filename=4next.{extension}; filename*=UTF-8''{quote(title + '.' + extension)}",
        "Cache-Control":"private, no-store"}


def items(value):
    try:
        return json.loads(value) if isinstance(value,str) else value or []
    except (ValueError,TypeError):
        return []


def lesson_markdown(lesson,language):
    ro = language == "ro"
    lines = [f"## {lesson['title']}","",lesson.get("short_summary") or "","",lesson.get("long_explanation") or "",""]
    for field,label in [("key_ideas","Idei principale" if ro else "Key ideas"),
        ("practical_insights","De reținut" if ro else "Practical insights"),
        ("examples","Exemple" if ro else "Examples"),("action_items","Exersează" if ro else "Practice")]:
        values = items(lesson.get(field))
        if values:
            lines.extend([f"### {label}","",*["- "+str(value) for value in values],""])
    if lesson.get("mermaid_diagram"):
        lines.extend(["```mermaid",lesson["mermaid_diagram"],"```",""])
    citations = items(lesson.get("source_citations"))
    if citations:
        lines.extend(["### Surse" if ro else "### Sources",""])
        for citation in citations:
            if isinstance(citation,dict):
                lines.append(f"- {'Pagina' if ro else 'Page'} {citation.get('page','?')}: {citation.get('text',citation.get('quote',''))}")
        lines.append("")
    return lines


@router.get("/course/{course_id}/markdown")
def export_course_markdown(course_id: str,user: dict | None=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        course = check_course_access(conn,course_id,user)
        lines = [f"# {course['title']}","",course.get("overview") or "",""]
        for row in conn.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY order_index,id",(course_id,)):
            lines.extend(lesson_markdown(dict(row),course["language"]))
        cards = conn.execute("SELECT * FROM flashcards WHERE course_id=?",(course_id,)).fetchall()
        if cards:
            lines.extend(["## Flashcarduri" if course["language"] == "ro" else "## Flashcards",""])
            for card in cards:
                lines.extend(["**"+card["question"]+"**",card["answer"],""])
    return Response("\n".join(lines),media_type="text/markdown; charset=utf-8",headers=attachment(course["title"],"md"))


@router.get("/course/{course_id}/anki")
def export_course_anki(course_id: str,user: dict | None=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        check_course_access(conn,course_id,user)
        rows = conn.execute("SELECT question,answer,category FROM flashcards WHERE course_id=?",(course_id,)).fetchall()
    # Plain-text mode prevents document content from being interpreted as HTML in Anki.
    lines = ["#separator:tab","#html:false","#tags column:3"]
    for row in rows:
        values = [str(row[field] or "").replace("\t"," ").replace("\n"," ") for field in ("question","answer","category")]
        lines.append("\t".join(values))
    return Response("\n".join(lines),media_type="text/tab-separated-values",headers=attachment("flashcards_anki","tsv"))


def media_export(lesson_id,user,kind,language=None):
    with closing(get_db_connection()) as conn:
        lesson,course = checked_lesson(conn,lesson_id,user)
    document_language = course["language"] or "en"
    if language is not None and language != document_language:
        raise HTTPException(400,"Exportul folosește limba documentului.")
    url = lesson.get(f"audio_url_{document_language}") or lesson.get("audio_url") if kind == "audio" else lesson.get("video_url")
    if not url or not url.startswith(f"/media/{kind}/"):
        raise HTTPException(404,"Fișierul nu a fost generat încă.")
    path = (MEDIA_DIR / url.removeprefix("/media/")).resolve()
    expected = (MEDIA_DIR / kind).resolve()
    if not path.is_relative_to(expected) or not path.is_file():
        raise HTTPException(404,"Fișierul nu a fost generat încă.")
    return FileResponse(path,media_type="audio/mpeg" if kind == "audio" else "video/mp4",
        headers=attachment(lesson["title"],"mp3" if kind == "audio" else "mp4"))


@router.get("/lesson/{lesson_id}/audio")
def export_lesson_audio(lesson_id: str,lang: str | None=None,user: dict | None=Depends(optional_user)):
    return media_export(lesson_id,user,"audio",lang)


@router.get("/lesson/{lesson_id}/video")
def export_lesson_video(lesson_id: str,user: dict | None=Depends(optional_user)):
    return media_export(lesson_id,user,"video")


@router.get("/lesson/{lesson_id}/diagram")
def export_lesson_diagram(lesson_id: str,user: dict | None=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        lesson,_ = checked_lesson(conn,lesson_id,user)
    if not lesson.get("mermaid_diagram"):
        raise HTTPException(404,"Această lecție nu are o diagramă.")
    return Response(lesson["mermaid_diagram"],media_type="text/vnd.mermaid",headers=attachment(lesson["title"],"mmd"))


@router.get("/lesson/{lesson_id}/text")
def export_lesson_text(lesson_id: str,user: dict | None=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        lesson,course = checked_lesson(conn,lesson_id,user)
        lines = lesson_markdown(lesson,course["language"])
        note = conn.execute("SELECT content FROM notes WHERE lesson_id=? AND user_id=?",(lesson_id,user["id"])).fetchone() if user else None
        if note:
            lines.extend(["## Notițele mele" if course["language"] == "ro" else "## My notes","",note["content"]])
    return Response("\n".join(lines),media_type="text/markdown; charset=utf-8",headers=attachment(lesson["title"],"md"))
