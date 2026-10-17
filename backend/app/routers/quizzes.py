import json
import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db_connection
from app.security import check_course_access, optional_user
from app.routers.courses import parse_json_fields
from app.schemas import QuizSubmissionSchema

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])

@router.get("/course/{course_id}")
def get_course_quizzes(course_id: str,user: dict | None=Depends(optional_user)):
    conn = get_db_connection()
    try:
        check_course_access(conn,course_id,user)
    except Exception:
        conn.close()
        raise
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE course_id = ?", (course_id,))
    rows = cursor.fetchall()
    quizzes = []
    for r in rows:
        q = dict(r)
        parse_json_fields(q,["source_citations"])
        if isinstance(q.get("options"), str):
            try:
                q["options"] = json.loads(q["options"])
            except Exception:
                q["options"] = []
        quizzes.append(q)
    conn.close()
    return quizzes

@router.post("/course/{course_id}/submit")
def submit_course_quiz(course_id: str, submission: QuizSubmissionSchema,user: dict | None=Depends(optional_user)):
    conn = get_db_connection()
    try:
        check_course_access(conn,course_id,user)
    except Exception:
        conn.close()
        raise
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE course_id = ?", (course_id,))
    rows = cursor.fetchall()
    if not rows:
        conn.close()
        raise HTTPException(status_code=404, detail="No quizzes found for this course")

    total = len(rows)
    correct_count = 0
    feedback = []

    for r in rows:
        q = dict(r)
        q_id = q["id"]
        opts = json.loads(q["options"]) if isinstance(q["options"], str) else q["options"]
        correct_idx = q["correct_index"]
        selected_idx = submission.answers.get(q_id, -1)

        is_correct = (selected_idx == correct_idx)
        if is_correct:
            correct_count += 1

        feedback.append({
            "quiz_id": q_id,
            "question": q["question"],
            "options": opts,
            "selected_index": selected_idx,
            "correct_index": correct_idx,
            "is_correct": is_correct,
            "explanation": q["explanation"]
        })

    percentage = round((correct_count / total) * 100, 1) if total > 0 else 0
    passed = percentage >= 70.0

    if user:
        cursor.execute("INSERT INTO quiz_attempts(id,user_id,course_id,score,total) VALUES(?,?,?,?,?)",
            ("attempt-"+uuid.uuid4().hex,user["id"],course_id,correct_count,total))
        conn.commit()

    conn.close()
    return {
        "score": correct_count,
        "total": total,
        "percentage": percentage,
        "passed": passed,
        "feedback": feedback
    }
