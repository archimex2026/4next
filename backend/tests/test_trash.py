"""Recycle-bin journeys run against temporary SQLite and owned UUID files only."""
import json
import sqlite3
import tempfile
import unittest
import uuid
from contextlib import closing
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import database
from app.main import app


class TrashJourneys(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.db_patch = patch.object(database, "DB_PATH", self.folder / "test.db")
        self.db_patch.start()
        database.init_db()
        self.owner, self.other, self.guest = TestClient(app), TestClient(app), TestClient(app)
        for client, name in [(self.owner,"owner"),(self.other,"other")]:
            response = client.post("/api/auth/register",json={"name":name,"email":name+"@trash.test",
                "password":"test passphrase 2026", "accept_terms":True})
            self.assertEqual(response.status_code,201,response.text)
        self.owner_id = self.owner.get("/api/auth/me").json()["user"]["id"]
        self.lesson_id = "lsn-" + uuid.uuid4().hex
        self.source = self.folder / "uploads" / (uuid.uuid4().hex + ".txt")
        self.audio = self.folder / "media" / "audio" / (self.lesson_id + "_en.mp3")
        self.source.parent.mkdir()
        self.audio.parent.mkdir(parents=True)
        self.source.write_text("Cells contain a membrane.",encoding="utf-8")
        self.audio.write_bytes(b"ID3-owned-test-audio")
        with closing(database.get_db_connection()) as conn:
            conn.execute("""INSERT INTO books(id,title,owner_id,visibility,file_path,source_text,source_pages,keywords)
                VALUES('b1','Cells',?,'public',?,?,?,?)""",(self.owner_id,str(self.source),self.source.read_text(),
                json.dumps([{"page":1,"text":self.source.read_text()}]),'["Cells"]'))
            conn.execute("INSERT INTO courses(id,book_id,title) VALUES('c1','b1','Cells')")
            conn.execute("INSERT INTO levels(id,course_id,level_number,title) VALUES('v1','c1',1,'Cells')")
            conn.execute("INSERT INTO lessons(id,course_id,level_id,order_index,title,audio_url) VALUES(?,'c1','v1',1,'Cells',?)",
                (self.lesson_id,"/media/audio/"+self.audio.name))
            conn.execute("INSERT INTO flashcards(id,course_id,question,answer) VALUES('f1','c1','Cell?','Life')")
            conn.execute("INSERT INTO quizzes(id,course_id,question,options,correct_index) VALUES('q1','c1','Cell?','[\"Life\",\"Rock\"]',0)")
            conn.commit()
        self.patches = [patch("app.services.trash.UPLOAD_DIR",self.source.parent),
            patch("app.services.trash.MEDIA_DIR",self.folder/"media"),patch("app.main.MEDIA_DIR",self.folder/"media")]
        # Start path overrides only after the intended RED endpoint check exists.
        self.paths_started = False

    def paths(self):
        if not self.paths_started:
            for override in self.patches:
                override.start()
            self.paths_started = True

    def tearDown(self):
        for client in (self.owner,self.other,self.guest):
            client.close()
        if self.paths_started:
            for override in reversed(self.patches):
                override.stop()
        self.db_patch.stop()
        self.temp.cleanup()

    def trash(self):
        response = self.owner.delete("/api/courses/c1")
        self.assertEqual(response.status_code,200,response.text)
        self.paths()
        return response.json()

    def test_owner_only_delete_trash_list_restore_and_permanent_delete(self):
        self.assertEqual(self.guest.delete("/api/courses/c1").status_code,401)
        self.assertEqual(self.other.delete("/api/courses/c1").status_code,404)
        self.assertEqual(self.guest.get("/api/trash").status_code,401)
        deleted = self.trash()
        self.assertEqual(deleted["status"],"trashed")
        self.assertEqual(self.other.get("/api/trash").json()["items"],[])
        for method,path in [("post","/api/trash/c1/restore"),("delete","/api/trash/c1")]:
            self.assertEqual(getattr(self.other,method)(path).status_code,404)
        result = self.owner.get("/api/trash").json()
        self.assertEqual(result["retention_days"],5)
        item = result["items"][0]
        self.assertEqual((item["id"],item["book_id"],item["title"]),("c1","b1","Cells"))
        start,end = [datetime.fromisoformat(item[key].replace("Z","+00:00")) for key in ("deleted_at","purge_at")]
        self.assertEqual((end-start).total_seconds(),5*86400)
        self.assertNotIn("file_path",item)

    def test_trashed_material_is_hidden_from_every_normal_access_path(self):
        self.trash()
        paths = ["/api/courses/c1","/api/books/b1","/api/study/c1/source","/api/study/c1/pdf",
            "/api/export/course/c1/markdown","/api/export/course/c1/anki","/api/lessons/"+self.lesson_id,
            "/api/flashcards/course/c1","/api/quizzes/course/c1","/media/audio/"+self.audio.name]
        for client in (self.owner,self.other,self.guest):
            self.assertEqual(client.get("/api/courses").json(),[])
            self.assertEqual(client.get("/api/books").json(),[])
            for path in paths:
                self.assertEqual(client.get(path).status_code,404,path)
        self.assertEqual(self.owner.patch("/api/books/b1/visibility",json={"visibility":"public"}).status_code,404)
        self.assertEqual(self.owner.post("/api/study/c1/chat",json={"message":"What is a cell?"}).status_code,404)
        self.assertTrue(self.source.is_file())
        self.assertTrue(self.audio.is_file())

    def test_restore_keeps_personal_work_but_requires_explicit_resharing(self):
        group = self.owner.post("/api/groups",json={"name":"Biology"}).json()
        self.other.post("/api/groups/join",json={"code":group["invite_code"]})
        self.owner.post(f"/api/groups/{group['id']}/materials",json={"course_id":"c1"})
        self.owner.post(f"/api/lessons/{self.lesson_id}/notes",json={"content":"Remember the membrane"})
        self.owner.post(f"/api/lessons/{self.lesson_id}/complete")
        self.trash()
        self.assertEqual(self.other.get(f"/api/groups/{group['id']}").json()["courses"],[])
        self.assertEqual(self.other.get("/api/groups").json()[0]["material_count"],0)
        response = self.owner.post("/api/trash/c1/restore")
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()["visibility"],"private")
        self.assertEqual(self.owner.get("/api/trash").json()["items"],[])
        lesson = self.owner.get("/api/lessons/"+self.lesson_id).json()
        self.assertEqual(lesson["notes"],"Remember the membrane")
        self.assertTrue(lesson["completed"])
        self.assertEqual(self.other.get("/api/courses/c1").status_code,404)
        self.assertEqual(self.guest.get("/api/courses/c1").status_code,404)
        self.assertEqual(self.owner.post("/api/trash/c1/restore").status_code,404)

    def test_permanent_delete_cascades_personal_rows_and_owned_files(self):
        self.owner.post(f"/api/lessons/{self.lesson_id}/notes",json={"content":"private notes"})
        self.owner.post(f"/api/lessons/{self.lesson_id}/complete")
        self.owner.post("/api/flashcards/f1/master")
        self.owner.post("/api/quizzes/course/c1/submit",json={"answers":{"q1":0}})
        self.other.post("/api/books/b1/rating",json={"stars":4})
        self.owner.post("/api/study/c1/highlights",json={"page":1,"start_offset":0,"end_offset":5,"text":"Cells"})
        self.assertEqual(self.owner.delete("/api/trash/c1").status_code,404)
        self.trash()
        response = self.owner.delete("/api/trash/c1")
        self.assertEqual(response.status_code,200,response.text)
        with closing(database.get_db_connection()) as conn:
            for table in ("books","courses","lessons","levels","notes","flashcards","quizzes","ratings",
                "highlights","quiz_attempts","user_lesson_progress","user_flashcard_progress"):
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM "+table).fetchone()[0],0,table)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],2)
        self.assertFalse(self.source.exists())
        self.assertFalse(self.audio.exists())

    def test_expiry_at_exactly_five_days_is_cleaned_by_next_request(self):
        self.trash()
        deadline = 2_000_000_000
        with closing(database.get_db_connection()) as conn:
            conn.execute("UPDATE books SET deleted_at=? WHERE id='b1'",(deadline-5*86400,))
            conn.commit()
        with patch("app.services.trash.time.time",return_value=deadline-1):
            from app.services.trash import purge_expired_materials
            purge_expired_materials()
        self.assertTrue(self.source.exists())
        # Auth session need not be valid for opportunistic public-request cleanup.
        with patch("app.services.trash.time.time",return_value=deadline):
            self.assertEqual(self.guest.get("/api/courses").status_code,200)
        self.assertFalse(self.source.exists())
        self.assertFalse(self.audio.exists())
        self.assertEqual(self.owner.post("/api/trash/c1/restore").status_code,404)

    def test_legacy_book_delete_is_soft_and_unsafe_file_paths_are_never_removed(self):
        outside = self.folder/"do-not-delete.txt"
        outside.write_text("unrelated",encoding="utf-8")
        self.paths()
        with closing(database.get_db_connection()) as conn:
            conn.execute("UPDATE books SET file_path=? WHERE id='b1'",(str(outside),))
            conn.execute("UPDATE lessons SET audio_url=? WHERE id=?",("/media/audio/../do-not-delete.txt",self.lesson_id))
            conn.commit()
        response = self.owner.delete("/api/books/b1")
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()["status"],"trashed")
        self.assertEqual(self.owner.delete("/api/trash/c1").status_code,200)
        self.assertTrue(outside.exists())

    def test_locked_upload_stays_queued_and_retries_on_next_request(self):
        self.trash()
        original_unlink = Path.unlink

        def locked_source(path,*args,**kwargs):
            if path == self.source:
                raise PermissionError("file temporarily locked")
            return original_unlink(path,*args,**kwargs)

        with patch.object(Path,"unlink",autospec=True,side_effect=locked_source):
            response = self.owner.delete("/api/trash/c1")
        self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(response.json()["cleanup_pending"])
        self.assertTrue(self.source.is_file())
        self.assertFalse(self.audio.exists())
        self.guest.get("/api/courses")
        self.assertFalse(self.source.exists())
        with closing(database.get_db_connection()) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM trash_file_cleanup").fetchone()[0],0)

    def test_database_delete_failure_rolls_back_notes_queue_and_material(self):
        self.owner.post(f"/api/lessons/{self.lesson_id}/notes",json={"content":"keep this note"})
        self.trash()
        with closing(database.get_db_connection()) as conn:
            conn.execute("""CREATE TRIGGER reject_delete BEFORE DELETE ON books
                BEGIN SELECT RAISE(ABORT,'test transaction rollback'); END""")
            conn.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.owner.delete("/api/trash/c1")
        with closing(database.get_db_connection()) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],1)
            self.assertEqual(conn.execute("SELECT content FROM notes").fetchone()[0],"keep this note")
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM trash_file_cleanup").fetchone()[0],0)
        self.assertTrue(self.source.exists())
        self.assertTrue(self.audio.exists())

    def test_audio_finishing_after_permanent_delete_does_not_recreate_orphan_media(self):
        self.paths()

        def delayed_audio(**kwargs):
            self.assertEqual(self.owner.delete("/api/courses/c1").status_code,200)
            self.assertEqual(self.owner.delete("/api/trash/c1").status_code,200)
            self.audio.write_bytes(b"late-generated-audio")
            return "/media/audio/"+self.audio.name,3,[]

        with patch("app.routers.lessons.generate_audio_lesson",side_effect=delayed_audio):
            response = self.owner.post(f"/api/lessons/{self.lesson_id}/generate-audio",json={"lang":"en"})
        self.assertEqual(response.status_code,404,response.text)
        self.assertFalse(self.audio.exists(),"generation must not resurrect a permanently deleted file")


if __name__ == "__main__":
    unittest.main()
