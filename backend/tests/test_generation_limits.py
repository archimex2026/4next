import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import database
from app.generation_limits import consume_budget, generation_slot
from app.services import audio_generator


class GenerationLimits(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.patch = patch.object(database, "DB_PATH", Path(self.folder.name)/"limits.db")
        self.patch.start()
        database.init_db()
        with closing(database.get_db_connection()) as conn:
            for user in ("alice", "bob", "chris", "dana"):
                conn.execute("INSERT INTO users(id,name,email,password_hash,terms_accepted_at) VALUES(?,?,?,'unused','now')",
                    (user,user,user+"@test.local"))
            conn.commit()

    def tearDown(self):
        self.patch.stop()
        self.folder.cleanup()

    def test_budgets_are_per_account_operation_and_window(self):
        with patch("app.generation_limits.time.time",return_value=864001):
            for _ in range(5):
                consume_budget("alice","upload")
            with self.assertRaises(HTTPException) as caught:
                consume_budget("alice","upload")
            self.assertEqual(caught.exception.status_code,429)
            consume_budget("bob","upload")
            consume_budget("alice","audio")
        with patch("app.generation_limits.time.time",return_value=864061):
            consume_budget("alice","upload")
        with closing(database.get_db_connection()) as conn:
            daily = conn.execute("SELECT requests FROM generation_usage WHERE user_id='alice' AND operation='upload' AND period=86400").fetchone()[0]
        self.assertEqual(daily,6)

    def test_daily_budget_cannot_be_bypassed_by_minute_windows(self):
        for minute in range(6):
            with patch("app.generation_limits.time.time",return_value=864001+minute*60):
                for _ in range(5):
                    consume_budget("alice","upload")
        with patch("app.generation_limits.time.time",return_value=864401):
            with self.assertRaises(HTTPException):
                consume_budget("alice","upload")
        with patch("app.generation_limits.time.time",return_value=950401):
            consume_budget("alice","upload")

    def test_concurrent_requests_are_rejected_and_slots_release_on_failure(self):
        with generation_slot("alice","upload"):
            with self.assertRaises(HTTPException):
                with generation_slot("alice","audio"):
                    self.fail("Same account entered two slots")
            with generation_slot("bob","upload"), generation_slot("chris","upload"):
                with self.assertRaises(HTTPException):
                    with generation_slot("dana","upload"):
                        self.fail("Global generation cap exceeded")
        with self.assertRaises(RuntimeError):
            with generation_slot("alice","upload"):
                raise RuntimeError("provider unavailable")
        with generation_slot("alice","upload"):
            pass


class NarrationIntegrity(unittest.TestCase):
    def test_failed_service_preserves_previous_audio_and_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(audio_generator,"AUDIO_DIR",Path(folder)):
            original = Path(folder)/"lesson_ro.mp3"
            original.write_bytes(b"previous real audio")
            def fail(script,voice,rate,language,path):
                path.write_bytes(b"partial")
                raise RuntimeError("offline")
            with patch.object(audio_generator,"_synthesize",side_effect=fail):
                with self.assertRaises(RuntimeError):
                    audio_generator.generate_audio_lesson("lesson","Titlu","Sursă",[],[])
            self.assertEqual(original.read_bytes(),b"previous real audio")
            self.assertEqual(list(Path(folder).iterdir()),[original])

    def test_audio_uses_same_language_and_only_given_lesson_content(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(audio_generator,"AUDIO_DIR",Path(folder)):
            scripts = []
            def synth(script,voice,rate,language,path):
                scripts.append((script,language))
                path.write_bytes(b"ID3"+b"test"*300)
            with patch.object(audio_generator,"_synthesize",side_effect=synth), patch.object(audio_generator,"get_audio_duration",return_value=12):
                result = audio_generator.generate_audio_lesson("lesson","Photosynthesis","Plants use light.",[],[],lang="en",return_details=True)
            self.assertEqual(scripts,[("Photosynthesis\n\nPlants use light.","en")])
            self.assertEqual(result[0],"/media/audio/lesson_en.mp3")
            self.assertEqual(result[1],12)
            with self.assertRaises(ValueError):
                audio_generator.generate_audio_lesson("lesson","T","S",[],[],lang="en",voice="ro-RO-AlinaNeural")


if __name__ == "__main__":
    unittest.main()
