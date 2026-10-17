import secrets
import uuid
from contextlib import closing
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from app.database import get_db_connection
from app.security import check_course_access, require_user, personal_completion

router = APIRouter(prefix="/api/groups", tags=["Study groups"])


class GroupCreate(BaseModel):
    name: str = Field(min_length=1,max_length=100)
    subject: str = Field(default="",max_length=160)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls,value):
        value = value.strip()
        if not value:
            raise ValueError("Dă un nume clasei.")
        return value


class GroupJoin(BaseModel):
    code: str = Field(min_length=6,max_length=32)


class ShareMaterial(BaseModel):
    course_id: str = Field(min_length=1,max_length=100)


def member_group(conn,group_id,user):
    row = conn.execute("""SELECT g.* FROM study_groups g JOIN group_members m ON m.group_id=g.id
        WHERE g.id=? AND m.user_id=?""",(group_id,user["id"])).fetchone()
    if not row:
        raise HTTPException(404,"Clasa nu a fost găsită.")
    return dict(row)


@router.get("")
def list_groups(user: dict = Depends(require_user)):
    with closing(get_db_connection()) as conn:
        rows = conn.execute("""SELECT g.*,
            (SELECT COUNT(*) FROM group_members WHERE group_id=g.id) member_count,
            (SELECT COUNT(*) FROM group_materials gm JOIN courses c ON c.id=gm.course_id
                JOIN books b ON b.id=c.book_id WHERE gm.group_id=g.id AND b.deleted_at IS NULL) material_count
            FROM study_groups g JOIN group_members m ON m.group_id=g.id WHERE m.user_id=? ORDER BY g.created_at DESC""",
            (user["id"],)).fetchall()
        return [dict(row) for row in rows]


@router.post("",status_code=201)
def create_group(data: GroupCreate,user: dict = Depends(require_user)):
    group_id = "grp-"+uuid.uuid4().hex
    code = secrets.token_hex(5).upper()
    with closing(get_db_connection()) as conn:
        conn.execute("INSERT INTO study_groups(id,owner_id,name,subject,invite_code) VALUES(?,?,?,?,?)",
            (group_id,user["id"],data.name,data.subject.strip(),code))
        conn.execute("INSERT INTO group_members(group_id,user_id) VALUES(?,?)",(group_id,user["id"]))
        conn.commit()
    return {"id":group_id,"owner_id":user["id"],"name":data.name,"subject":data.subject.strip(),"invite_code":code,"member_count":1,"material_count":0}


@router.post("/join")
def join_group(data: GroupJoin,user: dict = Depends(require_user)):
    with closing(get_db_connection()) as conn:
        row = conn.execute("SELECT * FROM study_groups WHERE invite_code=?",(data.code.strip().upper(),)).fetchone()
        if not row:
            raise HTTPException(404,"Codul de invitație nu este valid.")
        conn.execute("INSERT OR IGNORE INTO group_members(group_id,user_id) VALUES(?,?)",(row["id"],user["id"]))
        conn.commit()
        return dict(row)


@router.get("/{group_id}")
def get_group(group_id: str,user: dict = Depends(require_user)):
    with closing(get_db_connection()) as conn:
        group = member_group(conn,group_id,user)
        # Only names are shared with classmates; email and account preferences stay private.
        group["members"] = [dict(row) for row in conn.execute("""SELECT u.id,u.name,m.joined_at FROM users u
            JOIN group_members m ON m.user_id=u.id WHERE m.group_id=? ORDER BY m.joined_at""",(group_id,))]
        group["courses"] = [dict(row) for row in conn.execute("""SELECT c.*,b.cover_color,b.language document_language,b.visibility,b.owner_id,
            b.title book_title,gm.shared_by FROM courses c JOIN books b ON b.id=c.book_id
            JOIN group_materials gm ON gm.course_id=c.id
            JOIN group_members sharer ON sharer.group_id=gm.group_id AND sharer.user_id=gm.shared_by
            WHERE gm.group_id=? AND gm.shared_by=b.owner_id AND b.deleted_at IS NULL ORDER BY gm.created_at DESC""",(group_id,))]
        for course in group["courses"]:
            course["language"] = course.pop("document_language")
        group["member_count"] = len(group["members"])
        for course in group["courses"]:
            course["completion_percentage"] = personal_completion(conn,course["id"],user)
        group["material_count"] = len(group["courses"])
        return group


@router.post("/{group_id}/materials")
def share_material(group_id: str,data: ShareMaterial,user: dict = Depends(require_user)):
    with closing(get_db_connection()) as conn:
        member_group(conn,group_id,user)
        check_course_access(conn,data.course_id,user,write=True)
        conn.execute("INSERT OR IGNORE INTO group_materials(group_id,course_id,shared_by) VALUES(?,?,?)",(group_id,data.course_id,user["id"]))
        conn.commit()
    return {"status":"shared","group_id":group_id,"course_id":data.course_id}


@router.delete("/{group_id}/materials/{course_id}")
def revoke_material(group_id: str,course_id: str,user: dict = Depends(require_user)):
    with closing(get_db_connection()) as conn:
        group = member_group(conn,group_id,user)
        row = conn.execute("SELECT shared_by FROM group_materials WHERE group_id=? AND course_id=?",(group_id,course_id)).fetchone()
        if not row or user["id"] not in (group["owner_id"],row["shared_by"]):
            raise HTTPException(404,"Materialul partajat nu a fost găsit.")
        conn.execute("DELETE FROM group_materials WHERE group_id=? AND course_id=?",(group_id,course_id))
        conn.commit()
    return {"status":"revoked"}


@router.delete("/{group_id}/members/{user_id}")
def remove_member(group_id: str,user_id: str,user: dict = Depends(require_user)):
    with closing(get_db_connection()) as conn:
        group = member_group(conn,group_id,user)
        if user["id"] != group["owner_id"] and user_id != user["id"]:
            raise HTTPException(403,"Doar administratorul poate elimina alți membri.")
        if user_id == group["owner_id"]:
            raise HTTPException(400,"Administratorul nu poate părăsi clasa.")
        conn.execute("DELETE FROM group_materials WHERE group_id=? AND shared_by=?",(group_id,user_id))
        conn.execute("DELETE FROM group_members WHERE group_id=? AND user_id=?",(group_id,user_id))
        # A removed member must not regain access with the invitation they already know.
        code = secrets.token_hex(5).upper()
        conn.execute("UPDATE study_groups SET invite_code=? WHERE id=?",(code,group_id))
        conn.commit()
    return {"status":"removed", **({"invite_code":code} if user["id"] == group["owner_id"] else {})}
