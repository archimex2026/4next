from fastapi import APIRouter, HTTPException
from app.database import get_db_connection

router = APIRouter(prefix="/api/flashcards", tags=["Flashcards"])

@router.get("/course/{course_id}")
def get_course_flashcards(course_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM flashcards WHERE course_id = ?
    ORDER BY category ASC, id ASC
    """, (course_id,))
    cards = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return cards

@router.post("/{card_id}/master")
def toggle_card_mastered(card_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mastered FROM flashcards WHERE id = ?", (card_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Flashcard not found")

    new_mastered = 0 if row["mastered"] else 1
    cursor.execute("UPDATE flashcards SET mastered = ? WHERE id = ?", (new_mastered, card_id))
    conn.commit()
    conn.close()
    return {"card_id": card_id, "mastered": bool(new_mastered)}
