import unittest
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db
from app.services.demo_seeder import seed_demo_data

class TestBook2CourseAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        # Seed test data
        seed_demo_data(generate_media_assets=False)
        cls.client = TestClient(app)

    def test_01_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["app"], "Book2Course AI")
        self.assertEqual(data["status"], "ready")

    def test_02_system_status(self):
        response = self.client.get("/api/demo/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertTrue(data["demo_ready"])
        self.assertGreaterEqual(data["books_count"], 1)
        self.assertGreaterEqual(data["courses_count"], 1)

    def test_03_list_courses(self):
        response = self.client.get("/api/courses")
        self.assertEqual(response.status_code, 200)
        courses = response.json()
        self.assertIsInstance(courses, list)
        self.assertGreaterEqual(len(courses), 1)

    def test_04_get_course_detail(self):
        response = self.client.get("/api/courses/course-lean-startup")
        self.assertEqual(response.status_code, 200)
        course = response.json()
        self.assertEqual(course["id"], "course-lean-startup")
        self.assertIn("levels", course)
        self.assertEqual(len(course["levels"]), 3)
        self.assertIn("flashcards", course)
        self.assertIn("quizzes", course)

    def test_05_get_lesson(self):
        response = self.client.get("/api/lessons/lsn-ls-1")
        self.assertEqual(response.status_code, 200)
        lesson = response.json()
        self.assertEqual(lesson["id"], "lsn-ls-1")
        self.assertEqual(lesson["order_index"], 1)
        self.assertTrue(len(lesson["key_ideas"]) > 0)
        self.assertTrue(len(lesson["mermaid_diagram"]) > 0)

    def test_06_toggle_completion(self):
        response = self.client.post("/api/lessons/lsn-ls-1/complete")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("completed", data)

    def test_07_flashcards(self):
        response = self.client.get("/api/flashcards/course/course-lean-startup")
        self.assertEqual(response.status_code, 200)
        cards = response.json()
        self.assertGreaterEqual(len(cards), 10)

    def test_08_quiz_submission(self):
        # Submit correct answer for first question
        payload = {"answers": {"qz-test": 1}}
        response = self.client.post("/api/quizzes/course/course-lean-startup/submit", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("score", data)
        self.assertIn("total", data)
        self.assertIn("percentage", data)
        self.assertIn("feedback", data)

    def test_09_export_markdown(self):
        response = self.client.get("/api/export/course/course-lean-startup/markdown")
        self.assertEqual(response.status_code, 200)
        self.assertIn("The Lean Startup", response.text)
        self.assertIn("mermaid", response.text)

if __name__ == "__main__":
    unittest.main()
