from contextlib import closing
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.database import get_db_connection
from app.security import check_book_access, require_user

router = APIRouter(prefix="/api/books", tags=["Publishing"])


class Visibility(BaseModel):
    visibility: str = Field(pattern="^(private|public)$")


class Rating(BaseModel):
    stars: int = Field(ge=1,le=5,strict=True)


@router.patch("/{book_id}/visibility")
def set_visibility(book_id: str, data: Visibility, user: dict = Depends(require_user)):
    with closing(get_db_connection()) as conn:
        check_book_access(conn,book_id,user,write=True)
        conn.execute("UPDATE books SET visibility=? WHERE id=?",(data.visibility,book_id))
        conn.commit()
    return {"book_id":book_id,"visibility":data.visibility}


@router.post("/{book_id}/rating")
def rate_book(book_id: str, data: Rating, user: dict = Depends(require_user)):
    with closing(get_db_connection()) as conn:
        book = check_book_access(conn,book_id,user)
        if book["visibility"] != "public":
            raise HTTPException(400,"Poți evalua doar materialele publice.")
        if book["owner_id"] == user["id"]:
            raise HTTPException(400,"Poți evalua materialele altor persoane.")
        conn.execute("""INSERT INTO ratings(book_id,user_id,stars) VALUES(?,?,?)
            ON CONFLICT(book_id,user_id) DO UPDATE SET stars=excluded.stars,updated_at=CURRENT_TIMESTAMP""",
            (book_id,user["id"],data.stars))
        conn.commit()
        stats = conn.execute("SELECT ROUND(AVG(stars),1) rating_average,COUNT(*) rating_count FROM ratings WHERE book_id=?",(book_id,)).fetchone()
    return {"book_id":book_id,"user_rating":data.stars,**dict(stats)}
