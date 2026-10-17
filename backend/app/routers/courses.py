import json
from contextlib import closing
from typing import Literal
from fastapi import APIRouter, Depends, Query
from app.database import get_db_connection
from app.security import can_read_book, check_course_access, optional_user, personal_completion, safe_book

router = APIRouter(prefix="/api/courses", tags=["Courses"])


def parse_json_fields(item, fields):
    for field in fields:
        value = item.get(field)
        try:
            item[field] = json.loads(value) if isinstance(value,str) else value or []
        except (ValueError,TypeError):
            item[field] = []
    return item


def user_lesson(conn, lesson, user):
    item = parse_json_fields(dict(lesson), ["key_ideas","practical_insights","examples","action_items",
        "transcript","transcript_ro","transcript_en","source_citations"])
    progress = conn.execute("SELECT completed FROM user_lesson_progress WHERE user_id=? AND lesson_id=?",
        (user["id"],item["id"])).fetchone() if user else None
    item["completed"] = bool(progress["completed"]) if progress else False
    return item


def user_card(conn,card,user):
    item = parse_json_fields(dict(card),["source_citations"])
    progress = conn.execute("SELECT mastered FROM user_flashcard_progress WHERE user_id=? AND card_id=?",
        (user["id"],item["id"])).fetchone() if user else None
    item["mastered"] = bool(progress["mastered"]) if progress else False
    return item


@router.get("")
def list_courses(view: Literal["mine","public","all"]="all",q: str=Query(default="",max_length=200),
    user: dict | None=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        rows = conn.execute("""SELECT c.*,b.cover_color,b.author,b.page_count,b.title book_title,
            b.owner_id,b.visibility,b.language document_language,b.keywords,b.study_minutes,b.depth,b.generation_mode,
            COALESCE((SELECT ROUND(AVG(stars),1) FROM ratings WHERE book_id=b.id),0) rating_average,
            (SELECT COUNT(*) FROM ratings WHERE book_id=b.id) rating_count,
            (SELECT stars FROM ratings WHERE book_id=b.id AND user_id=?) user_rating
            FROM courses c JOIN books b ON b.id=c.book_id ORDER BY c.created_at DESC""",
            (user["id"] if user else "",)).fetchall()
        results = []
        # ponytail: one library scan for the prototype; paginate/filter in SQL when libraries grow.
        for row in rows:
            course = dict(row)
            course["language"] = course.pop("document_language")
            book_access = {"id":course["book_id"],"owner_id":course["owner_id"],"visibility":course["visibility"]}
            if not can_read_book(conn,book_access,user):
                continue
            if view == "mine" and (not user or course["owner_id"] != user["id"]):
                continue
            if view == "public" and course["visibility"] != "public":
                continue
            if q.strip() and q.strip().casefold() not in " ".join(str(course.get(field) or "") for field in ("title","book_title","author","keywords")).casefold():
                continue
            course["is_owner"] = bool(user and course["owner_id"] == user["id"])
            course["completion_percentage"] = personal_completion(conn,course["id"],user)
            parse_json_fields(course,["keywords"])
            results.append(course)
        return results


@router.get("/{course_id}")
def get_course_detail(course_id: str,user: dict | None=Depends(optional_user)):
    with closing(get_db_connection()) as conn:
        course = check_course_access(conn,course_id,user)
        book = dict(conn.execute("SELECT * FROM books WHERE id=?",(course["book_id"],)).fetchone())
        course["book"] = parse_json_fields(safe_book(book),["keywords"])
        course["is_owner"] = bool(user and book["owner_id"] == user["id"])
        course["keywords"] = course["book"]["keywords"]
        course["levels"] = []
        for row in conn.execute("SELECT * FROM levels WHERE course_id=? ORDER BY level_number",(course_id,)):
            level = dict(row)
            level["lessons"] = [user_lesson(conn,item,user) for item in conn.execute("SELECT * FROM lessons WHERE level_id=? ORDER BY order_index",(level["id"],))]
            course["levels"].append(level)
        course["flashcards"] = [user_card(conn,row,user) for row in conn.execute("SELECT * FROM flashcards WHERE course_id=?",(course_id,))]
        course["quizzes"] = [parse_json_fields(dict(row),["options","source_citations"]) for row in conn.execute("SELECT * FROM quizzes WHERE course_id=?",(course_id,))]
        course["completion_percentage"] = personal_completion(conn,course_id,user)
        stats = conn.execute("SELECT COALESCE(ROUND(AVG(stars),1),0) rating_average,COUNT(*) rating_count FROM ratings WHERE book_id=?",(course["book_id"],)).fetchone()
        course.update(dict(stats))
        return course


@router.get("/{course_id}/learning-path")
def get_learning_path(course_id: str,user: dict | None=Depends(optional_user)):
    course = get_course_detail(course_id,user)
    return {"course_id":course_id,"title":course["title"],"levels":course["levels"]}
