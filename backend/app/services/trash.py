"""Five-day recycle bin. SQLite owns deletion state and a retryable file-cleanup queue."""
import re
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from app.config import MEDIA_DIR, UPLOAD_DIR
from app.database import get_db_connection

RETENTION_DAYS = 5
RETENTION_SECONDS = RETENTION_DAYS * 86400


def utc_timestamp(epoch):
    return datetime.fromtimestamp(epoch,timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")


def deletion_dates(deleted_at):
    return {"deleted_at":utc_timestamp(deleted_at),"purge_at":utc_timestamp(deleted_at + RETENTION_SECONDS)}


def _cleanup_path(kind, name):
    """Only generated filenames directly under configured roots may be unlinked."""
    if kind == "upload":
        root = UPLOAD_DIR
        valid = re.fullmatch(r"[a-f0-9]{32}\.(?:pdf|epub|docx|txt|md)",name)
    else:
        root = MEDIA_DIR / kind
        extensions = {"audio":"mp3","video":"mp4","diagrams":"(?:png|svg|jpg|webp)"}
        valid = kind in extensions and re.fullmatch(r"lsn-[a-f0-9]{32}(?:_(?:ro|en))?\."+extensions[kind],name)
    if not valid:
        return None
    path = root / name
    try:
        if path.is_symlink() or path.resolve().parent != root.resolve():
            return None
    except (OSError,RuntimeError):
        return None
    return path


def _queue_owned_files(conn, book):
    stored = Path(book.get("file_path") or "")
    candidate = _cleanup_path("upload",stored.name)
    if candidate is not None:
        try:
            owned = stored.resolve() == candidate.resolve()
        except (OSError,RuntimeError):
            owned = False
        shared = conn.execute("SELECT 1 FROM books WHERE id<>? AND file_path=? LIMIT 1",(book["id"],str(stored))).fetchone()
        if owned and not shared:
            conn.execute("INSERT OR IGNORE INTO trash_file_cleanup(kind,name) VALUES('upload',?)",(stored.name,))
    for row in conn.execute("SELECT l.* FROM lessons l JOIN courses c ON c.id=l.course_id WHERE c.book_id=?",(book["id"],)):
        lesson_id = row["id"]
        if not re.fullmatch(r"lsn-[a-f0-9]{32}",lesson_id):
            continue  # Legacy/demo assets have no guaranteed exclusive UUID ownership.
        for kind, extensions in (("audio",("mp3",)),("video",("mp4",)),("diagrams",("png","svg","jpg","webp"))):
            suffixes = ("","_ro","_en") if kind == "audio" else ("",)
            for suffix in suffixes:
                for extension in extensions:
                    name = lesson_id + suffix + "." + extension
                    url = "/media/"+kind+"/"+name
                    shared = conn.execute("""SELECT 1 FROM lessons l JOIN courses c ON c.id=l.course_id
                        WHERE c.book_id<>? AND (l.audio_url=? OR l.audio_url_ro=? OR l.audio_url_en=? OR l.video_url=?) LIMIT 1""",
                        (book["id"],url,url,url,url)).fetchone()
                    if not shared and _cleanup_path(kind,name) is not None:
                        conn.execute("INSERT OR IGNORE INTO trash_file_cleanup(kind,name) VALUES(?,?)",(kind,name))


def _permanently_delete_book(conn, book):
    _queue_owned_files(conn,book)
    # Legacy notes predate foreign keys; all other dependent rows cascade from books.
    conn.execute("DELETE FROM notes WHERE course_id IN (SELECT id FROM courses WHERE book_id=?)",(book["id"],))
    conn.execute("DELETE FROM books WHERE id=?",(book["id"],))


def drain_file_cleanup():
    """Unlink after DB commit. Locked files remain queued across restarts for the next request."""
    with closing(get_db_connection()) as conn:
        for row in conn.execute("SELECT kind,name FROM trash_file_cleanup LIMIT 100").fetchall():
            path = _cleanup_path(row["kind"],row["name"])
            try:
                if path is not None:
                    path.unlink(missing_ok=True)
            except OSError:
                continue
            conn.execute("DELETE FROM trash_file_cleanup WHERE kind=? AND name=?",(row["kind"],row["name"]))
        conn.commit()
        return conn.execute("SELECT COUNT(*) FROM trash_file_cleanup").fetchone()[0]


def purge_expired_materials():
    """Called at startup and API access; no background timer or cron is implied."""
    cutoff = int(time.time()) - RETENTION_SECONDS
    with closing(get_db_connection()) as conn:
        if conn.execute("SELECT 1 FROM books WHERE deleted_at<=? LIMIT 1",(cutoff,)).fetchone():
            with conn:
                conn.execute("BEGIN IMMEDIATE")
                for row in conn.execute("SELECT * FROM books WHERE deleted_at<=?",(cutoff,)).fetchall():
                    _permanently_delete_book(conn,dict(row))
    drain_file_cleanup()


def move_book_to_trash(conn, book):
    deleted_at = int(time.time())
    conn.execute("UPDATE books SET deleted_at=?,visibility='private' WHERE id=?",(deleted_at,book["id"]))
    # Restoring never silently restores a public/group audience.
    conn.execute("DELETE FROM group_materials WHERE course_id IN (SELECT id FROM courses WHERE book_id=?)",(book["id"],))
    return {"status":"trashed","book_id":book["id"],**deletion_dates(deleted_at)}


def owned_trashed_course(conn, course_id, user):
    row = conn.execute("""SELECT b.* FROM books b JOIN courses c ON c.book_id=b.id
        WHERE c.id=? AND b.owner_id=? AND b.deleted_at>?""",
        (course_id,user["id"],int(time.time())-RETENTION_SECONDS)).fetchone()
    if not row:
        raise HTTPException(404,"Materialul nu se află în coșul tău sau termenul de restaurare a expirat.")
    return dict(row)
