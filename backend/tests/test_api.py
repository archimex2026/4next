"""Public demonstration and legacy migration checks using a disposable database."""
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import database
from app.main import app
from app.services.demo_seeder import seed_demo_data


class PublicDemoAPI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database_patch = patch.object(database, "DB_PATH", Path(self.temp.name) / "demo.db")
        self.database_patch.start()
        database.init_db()
        seed_demo_data(generate_media_assets=False)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.database_patch.stop()
        self.temp.cleanup()

    def test_authored_demos_have_real_sources_and_are_public(self):
        courses = self.client.get("/api/courses?view=public").json()
        self.assertEqual({c["id"] for c in courses}, {"course-demo-biologie", "course-demo-physics"})
        for course_id, language in [("course-demo-biologie","ro"),("course-demo-physics","en")]:
            result = self.client.get("/api/courses/" + course_id)
            self.assertEqual(result.status_code, 200, result.text)
            course = result.json()
            self.assertEqual(course["language"], language)
            self.assertEqual(course["visibility"], "public")
            source = self.client.get("/api/study/" + course_id + "/source").json()
            self.assertTrue(source["pages"][0]["text"])
            for level in course["levels"]:
                for lesson in level["lessons"]:
                    for citation in lesson["source_citations"]:
                        self.assertIn(citation["text"], source["pages"][0]["text"])

    def test_seed_is_idempotent_and_keeps_existing_materials(self):
        with closing(database.get_db_connection()) as conn:
            conn.execute("INSERT INTO books(id,title,visibility) VALUES('legacy-private','Original notes','private')")
            conn.commit()
        seed_demo_data(generate_media_assets=False)
        with closing(database.get_db_connection()) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM books").fetchone()[0], 3)
            self.assertEqual(conn.execute("SELECT title FROM books WHERE id='legacy-private'").fetchone()[0], "Original notes")
        self.assertNotIn("legacy-private", {c.get("book_id") for c in self.client.get("/api/courses").json()})

    def test_unknown_resources_are_errors_and_public_notes_require_account(self):
        self.assertEqual(self.client.get("/api/courses/missing").status_code, 404)
        course = self.client.get("/api/courses/course-demo-biologie").json()
        lesson_id = course["levels"][0]["lessons"][0]["id"]
        self.assertEqual(self.client.post(f"/api/lessons/{lesson_id}/notes", json={"content":"hello"}).status_code, 401)
        self.assertEqual(self.client.get(f"/api/lessons/{lesson_id}").status_code, 200)

    def test_source_pdf_contains_content(self):
        response = self.client.get("/api/study/course-demo-biologie/pdf?kind=source")
        self.assertEqual(response.status_code, 200, response.text[:200] if response.status_code != 200 else "")
        self.assertIn("application/pdf", response.headers["content-type"])
        self.assertTrue(response.content.startswith(b"%PDF-"))


class LegacyMigration(unittest.TestCase):
    def test_old_uploads_stay_private_and_known_demo_remains_public(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "legacy.db"
            with closing(sqlite3.connect(path)) as conn:
                conn.execute("""CREATE TABLE books(id TEXT PRIMARY KEY,title TEXT NOT NULL,author TEXT,
                    page_count INTEGER DEFAULT 0,file_path TEXT,file_name TEXT,file_type TEXT,file_size INTEGER,
                    cover_color TEXT,status TEXT,summary TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
                conn.execute("INSERT INTO books(id,title) VALUES('book-lean-startup','Old demo')")
                conn.execute("INSERT INTO books(id,title) VALUES('book-unclaimed-notes','Private old notes')")
                conn.commit()
            with patch.object(database,"DB_PATH",path):
                database.init_db()
                database.init_db()
                with closing(database.get_db_connection()) as conn:
                    values = {row["id"]:row["visibility"] for row in conn.execute("SELECT id,visibility FROM books")}
                self.assertEqual(values["book-lean-startup"],"public")
                self.assertEqual(values["book-unclaimed-notes"],"private")


if __name__ == "__main__":
    unittest.main()
