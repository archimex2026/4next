import json
from fastapi import APIRouter, HTTPException
from app.database import get_db_connection

router = APIRouter(prefix="/api/courses", tags=["Courses"])

@router.get("")
def list_courses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, b.cover_color, b.author, b.page_count, b.title as book_title
    FROM courses c
    JOIN books b ON c.book_id = b.id
    ORDER BY c.created_at DESC
    """)
    courses = [dict(row) for row in cursor.fetchall()]
    
    # Calculate completion for each
    for c in courses:
        cursor.execute("SELECT COUNT(*) as total, SUM(completed) as comp FROM lessons WHERE course_id = ?", (c["id"],))
        stats = cursor.fetchone()
        tot = stats["total"] or 0
        cmp = stats["comp"] or 0
        c["completion_percentage"] = round((cmp / tot) * 100) if tot > 0 else 0
        
    conn.close()
    return courses

@router.get("/{course_id}")
def get_course_detail(course_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get course
    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course_row = cursor.fetchone()
    if not course_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    course = dict(course_row)

    # Get book
    cursor.execute("SELECT * FROM books WHERE id = ?", (course["book_id"],))
    book_row = cursor.fetchone()
    course["book"] = dict(book_row) if book_row else None

    # Get levels
    cursor.execute("SELECT * FROM levels WHERE course_id = ? ORDER BY level_number ASC", (course_id,))
    levels = [dict(row) for row in cursor.fetchall()]

    for lvl in levels:
        cursor.execute("SELECT * FROM lessons WHERE level_id = ? ORDER BY order_index ASC", (lvl["id"],))
        lessons = []
        for l_row in cursor.fetchall():
            l_dict = dict(l_row)
            # Parse json strings safely
            for field in ["key_ideas", "practical_insights", "examples", "action_items", "transcript"]:
                val = l_dict.get(field)
                if val and isinstance(val, str):
                    try:
                        l_dict[field] = json.loads(val)
                    except Exception:
                        l_dict[field] = []
                elif not val:
                    l_dict[field] = []
            lessons.append(l_dict)
        lvl["lessons"] = lessons

    course["levels"] = levels

    # Get flashcards
    cursor.execute("SELECT * FROM flashcards WHERE course_id = ?", (course_id,))
    course["flashcards"] = [dict(row) for row in cursor.fetchall()]

    # Get quizzes
    cursor.execute("SELECT * FROM quizzes WHERE course_id = ?", (course_id,))
    quizzes = []
    for q_row in cursor.fetchall():
        q_dict = dict(q_row)
        if isinstance(q_dict.get("options"), str):
            try:
                q_dict["options"] = json.loads(q_dict["options"])
            except Exception:
                q_dict["options"] = []
        quizzes.append(q_dict)
    course["quizzes"] = quizzes

    # Completion calculation
    cursor.execute("SELECT COUNT(*) as total, SUM(completed) as comp FROM lessons WHERE course_id = ?", (course_id,))
    stats = cursor.fetchone()
    total_l = stats["total"] or 0
    comp_l = stats["comp"] or 0
    course["completion_percentage"] = round((comp_l / total_l) * 100) if total_l > 0 else 0

    conn.close()
    return course

@router.get("/{course_id}/learning-path")
def get_learning_path(course_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()
    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    cursor.execute("SELECT * FROM levels WHERE course_id = ? ORDER BY level_number ASC", (course_id,))
    levels = [dict(row) for row in cursor.fetchall()]

    for lvl in levels:
        cursor.execute("""
        SELECT id, order_index, title, short_summary, duration, completed, video_url, audio_url
        FROM lessons WHERE level_id = ? ORDER BY order_index ASC
        """, (lvl["id"],))
        lvl["lessons"] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return {
        "course_id": course_id,
        "title": course["title"],
        "levels": levels
    }
