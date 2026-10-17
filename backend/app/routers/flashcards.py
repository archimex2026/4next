from contextlib import closing
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db_connection
from app.security import check_course_access, optional_user, require_user
from app.routers.courses import user_card

router = APIRouter(prefix="/api/flashcards", tags=["Flashcards"])

@router.get("/course/{course_id}")
def get_course_flashcards(course_id: str,user: dict | None=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        check_course_access(conn,course_id,user)
        return [user_card(conn,row,user) for row in conn.execute("SELECT * FROM flashcards WHERE course_id=? ORDER BY category,id",(course_id,))]

@router.post("/{card_id}/master")
def toggle_card_mastered(card_id: str,user: dict=Depends(require_user)):
    with closing(get_db_connection()) as conn:
        card = conn.execute("SELECT course_id FROM flashcards WHERE id=?",(card_id,)).fetchone()
        if not card:
            raise HTTPException(404,"Flashcardul nu a fost găsit.")
        check_course_access(conn,card["course_id"],user)
        progress = conn.execute("SELECT mastered FROM user_flashcard_progress WHERE user_id=? AND card_id=?",(user["id"],card_id)).fetchone()
        mastered = 0 if progress and progress["mastered"] else 1
        conn.execute("""INSERT INTO user_flashcard_progress(user_id,card_id,mastered) VALUES(?,?,?)
            ON CONFLICT(user_id,card_id) DO UPDATE SET mastered=excluded.mastered,updated_at=CURRENT_TIMESTAMP""",(user["id"],card_id,mastered))
        conn.commit()
    return {"card_id":card_id,"mastered":bool(mastered)}
