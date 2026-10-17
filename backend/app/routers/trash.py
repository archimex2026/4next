"""Owner-only recycle bin. All normal resource access excludes deleted books."""
import time
from contextlib import closing
from fastapi import APIRouter, Depends
from app.database import get_db_connection
from app.security import require_user
from app.services.trash import (RETENTION_DAYS, RETENTION_SECONDS, deletion_dates,
    drain_file_cleanup, owned_trashed_course, _permanently_delete_book)

router = APIRouter(prefix="/api/trash",tags=["Recycle bin"])


@router.get("")
def list_trash(user=Depends(require_user)):
    with closing(get_db_connection()) as conn:
        rows = conn.execute("""SELECT c.id,c.book_id,c.title,COALESCE(c.subtitle,c.overview,'') description,
            b.deleted_at,b.cover_color,b.language FROM courses c JOIN books b ON b.id=c.book_id
            WHERE b.owner_id=? AND b.deleted_at>? ORDER BY b.deleted_at DESC,c.id""",
            (user["id"],int(time.time())-RETENTION_SECONDS)).fetchall()
    return {"items":[{**dict(row),**deletion_dates(row["deleted_at"])} for row in rows],"retention_days":RETENTION_DAYS}


@router.post("/{course_id}/restore")
def restore_material(course_id: str,user=Depends(require_user)):
    with closing(get_db_connection()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        book = owned_trashed_course(conn,course_id,user)
        conn.execute("UPDATE books SET deleted_at=NULL,visibility='private' WHERE id=?",(book["id"],))
    return {"status":"restored","course_id":course_id,"book_id":book["id"],"visibility":"private"}


@router.delete("/{course_id}")
def permanently_delete_material(course_id: str,user=Depends(require_user)):
    with closing(get_db_connection()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        book = owned_trashed_course(conn,course_id,user)
        _permanently_delete_book(conn,book)
    pending = drain_file_cleanup()
    return {"status":"deleted","course_id":course_id,"book_id":book["id"],"cleanup_pending":bool(pending)}
