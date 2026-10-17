import json
from fastapi import APIRouter, HTTPException, Response
from app.database import get_db_connection

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/course/{course_id}/markdown")
def export_course_markdown(course_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()
    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    cursor.execute("SELECT * FROM books WHERE id = ?", (course["book_id"],))
    book = cursor.fetchone()

    lines = [
        f"# {course['title']}",
        f"**Author:** {book['author'] if book else 'Expert'} | **Estimated Duration:** {course['estimated_duration']}",
        "",
        "## Course Overview",
        course["overview"],
        "",
        "---",
        ""
    ]

    cursor.execute("SELECT * FROM levels WHERE course_id = ? ORDER BY level_number ASC", (course_id,))
    levels = cursor.fetchall()

    for lvl in levels:
        lines.append(f"## {lvl['title']}")
        lines.append(f"*{lvl['description']}*")
        lines.append("")

        cursor.execute("SELECT * FROM lessons WHERE level_id = ? ORDER BY order_index ASC", (lvl["id"],))
        lessons = cursor.fetchall()

        for lsn in lessons:
            lines.append(f"### Lesson {lsn['order_index']}: {lsn['title']}")
            lines.append(f"**Summary:** {lsn['short_summary']}")
            lines.append("")
            lines.append("#### Long Explanation")
            lines.append(lsn["long_explanation"])
            lines.append("")

            # Key ideas
            ideas = json.loads(lsn["key_ideas"]) if lsn["key_ideas"] else []
            if ideas:
                lines.append("#### Key Principles")
                for item in ideas:
                    lines.append(f"- {item}")
                lines.append("")

            # Practical insights
            insights = json.loads(lsn["practical_insights"]) if lsn["practical_insights"] else []
            if insights:
                lines.append("#### Practical Insights")
                for item in insights:
                    lines.append(f"- {item}")
                lines.append("")

            # Examples
            examples = json.loads(lsn["examples"]) if lsn["examples"] else []
            if examples:
                lines.append("#### Case Studies & Examples")
                for item in examples:
                    lines.append(f"> {item}")
                lines.append("")

            # Action items
            actions = json.loads(lsn["action_items"]) if lsn["action_items"] else []
            if actions:
                lines.append("#### Action Checklist")
                for item in actions:
                    lines.append(f"- [ ] {item}")
                lines.append("")

            # Mermaid Diagram
            if lsn["mermaid_diagram"]:
                lines.append("#### Concept Diagram")
                lines.append("```mermaid")
                lines.append(lsn["mermaid_diagram"])
                lines.append("```")
                lines.append("")

            lines.append("---")
            lines.append("")

    # Flashcards section
    cursor.execute("SELECT * FROM flashcards WHERE course_id = ?", (course_id,))
    flashcards = cursor.fetchall()
    if flashcards:
        lines.append("## Flashcard Study Deck")
        for fc in flashcards:
            lines.append(f"**Q ({fc['category']}):** {fc['question']}")
            lines.append(f"**A:** {fc['answer']}")
            lines.append("")

    conn.close()

    content = "\n".join(lines)
    filename = f"{course['title'].replace(' ', '_')}_Complete_Guide.md"
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/course/{course_id}/anki")
def export_course_anki(course_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer, category FROM flashcards WHERE course_id = ?", (course_id,))
    rows = cursor.fetchall()
    conn.close()

    lines = ["#separator:tab", "#html:true", "#tags column:3"]
    for r in rows:
        q = r["question"].replace("\t", " ").replace("\n", " ")
        a = r["answer"].replace("\t", " ").replace("\n", " ")
        c = r["category"].replace(" ", "_")
        lines.append(f"{q}\t{a}\t{c}")

    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": "attachment; filename=flashcards_anki.tsv"}
    )

@router.get("/lesson/{lesson_id}/audio")
def export_lesson_audio(lesson_id: str, lang: str = "ro"):
    """Download the generated MP3 audio file for a lesson in Romanian or English."""
    from app.config import MEDIA_DIR
    from fastapi.responses import FileResponse
    from app.services.audio_generator import generate_audio_lesson

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Lesson not found")

    lesson = dict(row)
    conn.close()

    lang_code = "ro" if lang == "ro" else "en"
    audio_filename = f"{lesson_id}_{lang_code}.mp3"
    audio_path = MEDIA_DIR / "audio" / audio_filename

    # If file doesn't exist yet, generate it on demand
    if not audio_path.exists():
        try:
            generate_audio_lesson(
                lesson_id=lesson_id,
                title=lesson["title"],
                summary=lesson.get("short_summary", ""),
                key_ideas=json.loads(lesson.get("key_ideas", "[]")),
                examples=json.loads(lesson.get("examples", "[]")),
                long_explanation=lesson.get("long_explanation", ""),
                lang=lang_code
            )
        except Exception as e:
            # Check fallback default file
            fallback = MEDIA_DIR / "audio" / f"{lesson_id}.mp3"
            if fallback.exists():
                audio_path = fallback

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not ready")

    safe_title = "".join(c for c in lesson["title"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    download_name = f"{safe_title}_{lang_code.upper()}.mp3"
    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=download_name
    )

@router.get("/lesson/{lesson_id}/video")
def export_lesson_video(lesson_id: str):
    """Download the generated MP4 tutorial video for a lesson."""
    from app.config import MEDIA_DIR
    from fastapi.responses import FileResponse

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Lesson not found")

    lesson = dict(row)
    conn.close()

    video_path = MEDIA_DIR / "video" / f"{lesson_id}.mp4"
    if not video_path.exists():
        try:
            from app.services.video_generator import generate_video_lesson
            generate_video_lesson(
                lesson_id=lesson_id,
                lesson_title=lesson["title"],
                course_title="Course",
                summary=lesson.get("short_summary", ""),
                key_ideas=json.loads(lesson.get("key_ideas", "[]")),
                examples=json.loads(lesson.get("examples", "[]")),
                action_items=json.loads(lesson.get("action_items", "[]")),
                mermaid_diagram=lesson.get("mermaid_diagram", ""),
                audio_path=lesson.get("audio_url")
            )
        except Exception as e:
            print(f"On-demand video generation error: {e}")

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file is compiling, please retry in a few seconds.")

    safe_title = "".join(c for c in lesson["title"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"{safe_title}_Tutorial.mp4"
    )

@router.get("/lesson/{lesson_id}/diagram")
def export_lesson_diagram(lesson_id: str):
    """Download the Mermaid UML architectural diagram for a lesson."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title, mermaid_diagram FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Lesson not found")

    diagram_content = row["mermaid_diagram"] or "graph TD\n  A[Start] --> B[End]"
    safe_title = "".join(c for c in row["title"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    
    return Response(
        content=diagram_content,
        media_type="text/vnd.mermaid",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_diagram.mmd"}
    )

@router.get("/lesson/{lesson_id}/text")
def export_lesson_text(lesson_id: str):
    """Download complete lesson transcript, key principles, and notes as Markdown."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Lesson not found")

    lesson = dict(row)
    
    # Get notes
    cursor.execute("SELECT content FROM notes WHERE lesson_id = ?", (lesson_id,))
    note_row = cursor.fetchone()
    notes = note_row["content"] if note_row else ""
    conn.close()

    key_ideas = json.loads(lesson.get("key_ideas", "[]")) if lesson.get("key_ideas") else []
    practical_insights = json.loads(lesson.get("practical_insights", "[]")) if lesson.get("practical_insights") else []
    examples = json.loads(lesson.get("examples", "[]")) if lesson.get("examples") else []
    action_items = json.loads(lesson.get("action_items", "[]")) if lesson.get("action_items") else []

    lines = [
        f"# {lesson['title']}",
        f"**Durată estimată:** {lesson.get('duration', '4 mins')}",
        "",
        "## Sinteză Executivă",
        lesson.get("short_summary", ""),
        "",
        "## Explicație Detaliată",
        lesson.get("long_explanation", ""),
        "",
        "## Principii & Reguli Fundamentale",
        *[f"- {ki}" for ki in key_ideas],
        "",
        "## Perspective Practice",
        *[f"- {pi}" for pi in practical_insights],
        "",
        "## Studii de Caz & Exemple",
        *[f"> {ex}" for ex in examples],
        "",
        "## Plan de Acțiune",
        *[f"- [ ] {act}" for act in action_items],
        "",
        "## Diagramă Arhitecturală Mermaid UML",
        "```mermaid",
        lesson.get("mermaid_diagram", ""),
        "```",
        ""
    ]

    if notes:
        lines.extend([
            "## Notițe Personale Salvează",
            notes,
            ""
        ])

    safe_title = "".join(c for c in lesson["title"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    return Response(
        content="\n".join(lines),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_Notite_Complete.md"}
    )
