"""Shared session and resource-access boundary for every API and media route."""
import hashlib
import hmac
import secrets
import time
from contextlib import closing
from fastapi import HTTPException, Request
from app.config import SESSION_COOKIE_NAME
from app.database import get_db_connection

USER_FIELDS = "id, name, email, study_minutes, depth, exam_goal"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def optional_user(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    with closing(get_db_connection()) as conn:
        row = conn.execute(f"SELECT {', '.join('u.' + name.strip() for name in USER_FIELDS.split(','))} "
            "FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>?",
            (token_hash(token), int(time.time()))).fetchone()
    return dict(row) if row else None


def require_user(request: Request) -> dict:
    user = optional_user(request)
    if user is None:
        raise HTTPException(401, "Conectează-te pentru a salva și organiza materialele tale.")
    return user


def can_read_book(conn, book: dict, user: dict | None) -> bool:
    if book["visibility"] == "public":
        return True
    if not user:
        return False
    if book.get("owner_id") == user["id"]:
        return True
    return conn.execute("""SELECT 1 FROM group_materials gm
        JOIN group_members member ON member.group_id=gm.group_id
        JOIN group_members sharer ON sharer.group_id=gm.group_id AND sharer.user_id=gm.shared_by
        JOIN courses c ON c.id=gm.course_id
        WHERE c.book_id=? AND member.user_id=? AND gm.shared_by=? LIMIT 1""",
        (book["id"], user["id"], book["owner_id"])).fetchone() is not None


def check_book_access(conn, book_id: str, user: dict | None, write: bool = False) -> dict:
    row = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    book = dict(row) if row else None
    allowed = book and ((user and book.get("owner_id") == user["id"]) if write else can_read_book(conn, book, user))
    if not allowed:
        raise HTTPException(404, "Materialul nu a fost găsit sau nu ai acces la el.")
    return book


def check_course_access(conn, course_id: str, user: dict | None, write: bool = False) -> dict:
    row = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Cursul nu a fost găsit.")
    course = dict(row)
    book = check_book_access(conn, course["book_id"], user, write)
    course.update({key: book.get(key) for key in ("owner_id", "visibility", "language", "study_minutes", "depth", "generation_mode")})
    return course


def personal_completion(conn, course_id: str, user: dict | None) -> int:
    if not user:
        return 0
    row = conn.execute("""SELECT COUNT(*) total, COALESCE(SUM(p.completed),0) completed FROM lessons l
        LEFT JOIN user_lesson_progress p ON p.lesson_id=l.id AND p.user_id=? WHERE l.course_id=?""",
        (user["id"], course_id)).fetchone()
    return round(row["completed"] / row["total"] * 100) if row["total"] else 0


def safe_book(book: dict) -> dict:
    """Filesystem paths and raw source text belong only to dedicated guarded source endpoints."""
    return {key: value for key, value in book.items() if key not in ("file_path", "source_text", "source_pages")}
