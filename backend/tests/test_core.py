"""Account, sharing and privacy journeys against a disposable SQLite database."""
import json
import sys
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import database
from app.main import app


class CoreJourneys(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(database, "DB_PATH", Path(self.temp.name) / "test.db")
        self.db_patch.start()
        database.init_db()
        self.alice = TestClient(app)
        self.bob = TestClient(app)
        self.guest = TestClient(app)

    def tearDown(self):
        self.db_patch.stop()
        self.temp.cleanup()

    def register(self, client, email="alice@example.test"):
        result = client.post("/api/auth/register", json={"name": "Student", "email": email,
            "password": "a long passphrase 42", "accept_terms": True})
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()["user"]

    def material(self, owner=None, visibility="private", suffix="1"):
        with closing(database.get_db_connection()) as conn:
            conn.execute("INSERT INTO books(id,title,owner_id,visibility,language) VALUES(?,?,?,?,?)",
                ("b" + suffix, "Biology", owner, visibility, "en"))
            conn.execute("INSERT INTO courses(id,book_id,title) VALUES(?,?,?)", ("c" + suffix,"b" + suffix,"Biology"))
            conn.execute("INSERT INTO levels(id,course_id,level_number,title) VALUES(?,?,1,'Cells')", ("v" + suffix,"c" + suffix))
            conn.execute("INSERT INTO lessons(id,course_id,level_id,order_index,title,key_ideas) VALUES(?,?,?,1,'Cell membranes','[]')",
                ("l" + suffix,"c" + suffix,"v" + suffix))
            conn.execute("INSERT INTO flashcards(id,course_id,question,answer) VALUES(?,?,'Cell?','Unit of life')", ("f" + suffix,"c" + suffix))
            conn.execute("INSERT INTO quizzes(id,course_id,question,options,correct_index) VALUES(?,?,?, ?,0)",
                ("q" + suffix,"c" + suffix,"Cell?", json.dumps(["Unit of life","Rock"])))
            conn.commit()

    def test_account_session_profile_logout(self):
        user = self.register(self.alice)
        self.assertEqual(self.alice.get("/api/auth/me").json()["user"]["id"], user["id"])
        self.assertIn("HttpOnly", self.alice.post("/api/auth/login", json={"email": user["email"], "password": "a long passphrase 42"}).headers["set-cookie"])
        self.assertEqual(self.alice.patch("/api/auth/profile", json={"study_minutes": 35, "depth": "deep", "exam_goal": "BAC"}).status_code, 200)
        self.assertEqual(self.alice.get("/api/auth/me").json()["user"]["exam_goal"], "BAC")
        self.assertEqual(self.alice.post("/api/auth/logout").status_code, 200)
        self.assertIsNone(self.alice.get("/api/auth/me").json()["user"])
        with closing(database.get_db_connection()) as conn:
            stored = conn.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()[0]
        self.assertNotIn("a long passphrase", stored)

    def test_registration_terms_password_and_duplicate_validation(self):
        payload = {"name":"Student", "email":"alice@example.test", "password":"short", "accept_terms":False}
        self.assertEqual(self.alice.post("/api/auth/register", json=payload).status_code, 422)
        self.register(self.alice)
        result = self.bob.post("/api/auth/register", json={**payload,"password":"a long passphrase 42","accept_terms":True})
        self.assertEqual(result.status_code, 409)

    def test_private_routes_are_hidden_then_publish_and_rating(self):
        user = self.register(self.alice)
        self.register(self.bob, "bob@example.test")
        self.material(user["id"])
        paths = ["/api/courses/c1", "/api/courses/c1/learning-path", "/api/lessons/l1",
            "/api/flashcards/course/c1", "/api/quizzes/course/c1", "/api/export/course/c1/anki", "/api/export/lesson/l1/text"]
        for path in paths:
            self.assertEqual(self.bob.get(path).status_code, 404, path)
            self.assertEqual(self.alice.get(path).status_code, 200, path)
        self.assertEqual(self.guest.get("/api/courses").json(), [])
        self.assertEqual(self.bob.patch("/api/books/b1/visibility", json={"visibility":"public"}).status_code, 404)
        self.assertEqual(self.alice.patch("/api/books/b1/visibility", json={"visibility":"public"}).status_code, 200)
        self.assertEqual(self.guest.get("/api/courses/c1").status_code, 200)
        self.assertEqual(self.bob.post("/api/books/b1/rating", json={"stars":5}).status_code, 200)
        self.assertEqual(self.bob.post("/api/books/b1/rating", json={"stars":3}).status_code, 200)
        listed = self.guest.get("/api/courses?view=public&q=Biology").json()[0]
        self.assertEqual((listed["rating_average"], listed["rating_count"]), (3,1))
        self.assertEqual(self.bob.post("/api/books/b1/rating", json={"stars":6}).status_code, 422)

    def test_progress_mastery_and_notes_belong_to_each_student(self):
        self.register(self.alice)
        self.register(self.bob, "bob@example.test")
        self.material(None,"public")
        self.assertEqual(self.alice.post("/api/lessons/l1/complete").status_code, 200)
        self.assertEqual(self.alice.post("/api/lessons/l1/notes", json={"content":"my private notes"}).status_code, 200)
        self.assertEqual(self.alice.post("/api/flashcards/f1/master").status_code, 200)
        self.assertTrue(self.alice.get("/api/lessons/l1").json()["completed"])
        self.assertFalse(self.bob.get("/api/lessons/l1").json()["completed"])
        self.assertEqual(self.bob.get("/api/lessons/l1").json()["notes"], "")
        self.assertNotIn("my private notes", self.bob.get("/api/export/lesson/l1/text").text)
        self.assertFalse(self.bob.get("/api/flashcards/course/c1").json()[0]["mastered"])
        self.assertEqual(self.guest.post("/api/lessons/l1/complete").status_code, 401)

    def test_group_sharing_is_explicit_and_revocable(self):
        user = self.register(self.alice)
        self.register(self.bob,"bob@example.test")
        self.material(user["id"])
        group = self.alice.post("/api/groups",json={"name":"Biology club","subject":"Biology"}).json()
        self.assertIn("invite_code", group)
        self.assertEqual(self.bob.post("/api/groups/join",json={"code":group["invite_code"]}).status_code,200)
        self.assertEqual(self.bob.get("/api/courses/c1").status_code,404)
        self.assertEqual(self.alice.post(f"/api/groups/{group['id']}/materials",json={"course_id":"c1"}).status_code,200)
        self.assertEqual(self.bob.get("/api/courses/c1").status_code,200)
        self.assertEqual(self.guest.get("/api/courses/c1").status_code,404)
        self.alice.post("/api/lessons/l1/complete")
        self.assertEqual(self.alice.get(f"/api/groups/{group['id']}").json()["courses"][0]["completion_percentage"],100)
        self.assertEqual(self.bob.get(f"/api/groups/{group['id']}").json()["courses"][0]["completion_percentage"],0)
        self.assertEqual(self.alice.delete(f"/api/groups/{group['id']}/materials/c1").status_code,200)
        self.assertEqual(self.bob.get("/api/courses/c1").status_code,404)

    def test_cross_origin_mutations_and_destructive_demo_are_blocked(self):
        self.assertEqual(self.alice.post("/api/auth/register",headers={"Origin":"https://evil.example"},json={"name":"A","email":"a@b.test","password":"long password 123","accept_terms":True}).status_code,403)
        self.assertEqual(self.alice.post("/api/demo/reset").status_code,403)
        self.assertEqual(self.alice.post("/api/demo/seed").status_code,403)
        self.assertNotIn("db_location",self.guest.get("/api/demo/status").json())

    def test_removed_member_cannot_reuse_the_old_invitation(self):
        owner = self.register(self.alice)
        member = self.register(self.bob, "bob@example.test")
        self.material(owner["id"])
        group = self.alice.post("/api/groups",json={"name":"Exam study","subject":"Biology"}).json()
        code = group["invite_code"]
        self.assertEqual(self.bob.post("/api/groups/join",json={"code":code}).status_code,200)
        self.alice.post(f"/api/groups/{group['id']}/materials",json={"course_id":"c1"})
        self.assertEqual(self.bob.get("/api/courses/c1").status_code,200)
        result = self.alice.delete(f"/api/groups/{group['id']}/members/{member['id']}")
        self.assertEqual(result.status_code,200)
        self.assertNotEqual(result.json()["invite_code"],code)
        self.assertEqual(self.bob.post("/api/groups/join",json={"code":code}).status_code,404)
        self.assertEqual(self.bob.get("/api/courses/c1").status_code,404)
        self.assertEqual(self.bob.get(f"/api/groups/{group['id']}").status_code,404)

    def test_quiz_scores_are_source_based_and_attempts_belong_to_account(self):
        owner = self.register(self.alice)
        self.register(self.bob, "bob@example.test")
        self.material(owner["id"])
        self.assertEqual(self.bob.post("/api/quizzes/course/c1/submit",json={"answers":{"q1":0}}).status_code,404)
        correct = self.alice.post("/api/quizzes/course/c1/submit",json={"answers":{"q1":0}})
        self.assertEqual(correct.status_code,200)
        self.assertEqual(correct.json()["percentage"],100)
        self.assertTrue(correct.json()["feedback"][0]["is_correct"])
        wrong = self.alice.post("/api/quizzes/course/c1/submit",json={"answers":{"q1":1}})
        self.assertEqual(wrong.json()["percentage"],0)
        self.assertFalse(wrong.json()["passed"])
        from contextlib import closing
        with closing(database.get_db_connection()) as conn:
            rows = conn.execute("SELECT user_id,score FROM quiz_attempts ORDER BY score").fetchall()
            self.assertEqual([(row["user_id"],row["score"]) for row in rows],[(owner["id"],0),(owner["id"],1)])

    def test_audio_language_is_fixed_and_generation_requires_owner(self):
        user = self.register(self.alice)
        self.register(self.bob,"bob@example.test")
        self.material(user["id"],"public")
        self.assertEqual(self.bob.post("/api/lessons/l1/generate-audio",json={"lang":"en"}).status_code,404)
        self.assertEqual(self.alice.post("/api/lessons/l1/generate-audio",json={"lang":"ro"}).status_code,400)
        self.assertEqual(self.alice.post("/api/lessons/l1/language/ro").status_code,400)

    def test_media_checks_access_for_each_request(self):
        user = self.register(self.alice)
        self.material(user["id"])
        with tempfile.TemporaryDirectory() as media:
            path = Path(media)/"audio"
            path.mkdir()
            (path/"l1_en.mp3").write_bytes(b"ID3-test")
            with patch("app.main.MEDIA_DIR", Path(media)):
                self.assertEqual(self.guest.get("/media/audio/l1_en.mp3").status_code,404)
                self.assertEqual(self.alice.get("/media/audio/l1_en.mp3").status_code,200)
                self.assertEqual(self.alice.get("/media/audio/not-a-lesson.mp3").status_code,404)

    def test_expired_sessions_do_not_authenticate_and_login_is_throttled(self):
        user = self.register(self.alice)
        with closing(database.get_db_connection()) as conn:
            conn.execute("UPDATE sessions SET expires_at=0 WHERE user_id=?",(user["id"],))
            conn.commit()
        self.assertIsNone(self.alice.get("/api/auth/me").json()["user"])
        for _ in range(8):
            self.assertEqual(self.alice.post("/api/auth/login",json={"email":user["email"],"password":"incorrect"}).status_code,401)
        self.assertEqual(self.alice.post("/api/auth/login",json={"email":user["email"],"password":"incorrect"}).status_code,429)

    def test_legacy_migration_preserves_data_and_keeps_unassigned_uploads_private(self):
        with tempfile.TemporaryDirectory() as location:
            legacy_path = Path(location)/"legacy.db"
            with closing(sqlite3.connect(legacy_path)) as conn:
                conn.execute("CREATE TABLE books(id TEXT PRIMARY KEY,title TEXT NOT NULL)")
                conn.executemany("INSERT INTO books(id,title) VALUES(?,?)",[("book-lean-startup","Demo"),("private-legacy","Legacy notes")])
                conn.commit()
            with patch.object(database,"DB_PATH",legacy_path):
                database.init_db()
                database.init_db()
                with closing(database.get_db_connection()) as conn:
                    rows = {row["id"]:dict(row) for row in conn.execute("SELECT * FROM books")}
                    self.assertEqual(rows["private-legacy"]["title"],"Legacy notes")
                    self.assertEqual(rows["private-legacy"]["visibility"],"private")
                    self.assertEqual(rows["book-lean-startup"]["visibility"],"public")


if __name__ == "__main__":
    unittest.main()
