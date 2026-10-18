"""Full-size authored fixture, atomic continuation, and retry/access regressions."""
import json
import sys
import asyncio
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app import database
from app.main import app
from app.services.segmented_generation import plan_segments, segment_pages, segment_target

TEXT = ('A variable stores a value of a particular type. The type determines which operations can be used. '
        'A constant cannot be assigned a different value after initialization. Loops repeat a statement while a condition holds. ')
PAGES = [{'page': i, 'text': TEXT.replace('variable', f'variable from section {i}')
    .replace('A constant', f'The constant from section {i}').replace('Loops', f'Loops in section {i}') * 2}
    for i in range(1, 128)]


class SegmentPlanTests(unittest.TestCase):
    def test_blank_segment_does_not_fabricate_a_lesson_or_call_a_provider(self):
        from app.services.ai_analyzer import analyze_book_with_gemini
        with patch('app.services.ai_analyzer.gemini_json') as provider:
            course = asyncio.run(analyze_book_with_gemini('Programming', '', '', 'en', [{'page': 1, 'text': ''}]))
        self.assertEqual(course['levels'], [])
        self.assertEqual(course['quizzes'], [])
        provider.assert_not_called()

    def test_every_character_and_blank_page_is_planned_once_with_bounded_parts(self):
        pages = PAGES + [{'page': 128, 'text': ''}, {'page': 129, 'text': ('A long line of code and prose.\n' * 1600)}]
        plan = plan_segments(pages, 120)
        reconstructed = {p['page']: '' for p in pages}
        for segment in plan:
            part = segment_pages(segment, pages)
            self.assertLessEqual(len({p['page'] for p in part}), 12)
            self.assertLessEqual(sum(len(p['text']) for p in part), 12000)
            for page in part:
                reconstructed[page['page']] += page['text']
        self.assertEqual(reconstructed, {p['page']: p['text'] for p in pages})
        self.assertEqual(sum(s['study_minutes'] for s in plan), 120)

    def test_longer_session_increases_the_requested_teaching_not_just_the_label(self):
        brief, extended = plan_segments(PAGES, 20), plan_segments(PAGES, 120)
        self.assertEqual(len(brief), len(extended))
        self.assertGreater(sum(map(segment_target, extended)), sum(map(segment_target, brief)))
        self.assertEqual(plan_segments(PAGES[:22], 120), [])


class SegmentAPITests(unittest.TestCase):
    def test_duplicate_explanation_does_not_claim_pages_without_saved_lesson_citations(self):
        from app.services.ai_analyzer import build_content_aware_curriculum
        with closing(database.get_db_connection()) as conn:
            explanation = conn.execute('SELECT long_explanation FROM lessons WHERE course_id=? LIMIT 1', (self.course_id,)).fetchone()[0]
        curriculum = build_content_aware_curriculum('Programming', '', PAGES[12]['text'], 'en', [PAGES[12]])
        curriculum['levels'][0]['lessons'] = curriculum['levels'][0]['lessons'][:1]
        curriculum['levels'][0]['lessons'][0]['long_explanation'] = explanation
        curriculum['flashcards'], curriculum['quizzes'] = [], []
        with patch('app.routers.study.analyze_book_with_gemini', return_value=curriculum):
            response = self.owner.post(self.base+'/generate-next', json={'segment_index': 1})
        self.assertEqual(response.status_code, 200, response.text)
        part = response.json()['segments'][1]
        self.assertEqual(part['lesson_count'], 0)
        self.assertEqual(part['cited_pages'], [])
        self.assertNotIn(13, response.json()['cited_pages'])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.uploads = self.root / 'uploads'
        self.uploads.mkdir()
        self.patches = [patch.object(database, 'DB_PATH', self.root / 'test.db'),
            patch('app.routers.books.UPLOAD_DIR', self.uploads), patch('app.services.study_ai.GEMINI_API_KEY', '')]
        for item in self.patches:
            item.start()
        database.init_db()
        self.owner = TestClient(app, raise_server_exceptions=False)
        self.other = TestClient(app)
        self.anon = TestClient(app)
        for client, name in [(self.owner, 'owner'), (self.other, 'reader')]:
            response = client.post('/api/auth/register', json={'name': name, 'email': name+'@example.com',
                'password': 'secure-password-123', 'accept_terms': True})
            self.assertEqual(response.status_code, 201)
        source = {'title': 'Programming', 'pages': PAGES, 'text': '\n\n'.join(p['text'] for p in PAGES),
                  'page_count': 127, 'page_kind': 'page'}
        with patch('app.routers.books.extract_document', return_value=source):
            response = self.owner.post('/api/books/upload', data={'text': TEXT, 'study_minutes': 120, 'language': 'en'})
        self.assertEqual(response.status_code, 200, response.text)
        self.book_id, self.course_id = response.json()['book_id'], response.json()['course_id']
        self.base = '/api/study/'+self.course_id

    def tearDown(self):
        for client in [self.owner, self.other, self.anon]:
            client.close()
        for item in reversed(self.patches):
            item.stop()
        self.folder.cleanup()

    def progress(self):
        return self.owner.get(self.base+'/source').json()['generation_progress']

    def test_complete_127_page_plan_and_replay_preserve_materials_notes_and_progress(self):
        initial = self.progress()
        self.assertEqual((initial['completed'], initial['total']), (1, 11))
        self.assertEqual(initial['processed_pages'], list(range(1, 13)))
        with closing(database.get_db_connection()) as conn, conn:
            lesson = conn.execute('SELECT id FROM lessons WHERE course_id=?', (self.course_id,)).fetchone()[0]
            user_id = conn.execute("SELECT id FROM users WHERE email='owner@example.com'").fetchone()[0]
            conn.execute('INSERT INTO user_lesson_progress(user_id,lesson_id,completed) VALUES(?,?,1)', (user_id, lesson))
            conn.execute("INSERT INTO notes(id,course_id,lesson_id,user_id,content) VALUES('note',?,?,?,'Keep this note')", (self.course_id,lesson,user_id))
        current = initial
        while current['next_index'] is not None:
            response = self.owner.post(self.base+'/generate-next', json={'segment_index': current['next_index']})
            self.assertEqual(response.status_code, 200, response.text)
            current = response.json()
        self.assertEqual(current['processed_pages'], list(range(1, 128)))
        with patch('app.routers.study.analyze_book_with_gemini') as provider:
            self.assertEqual(self.owner.post(self.base+'/generate-next', json={'segment_index': 1}).json(), current)
            provider.assert_not_called()
        with closing(database.get_db_connection()) as conn:
            self.assertEqual(conn.execute('SELECT completed FROM user_lesson_progress WHERE lesson_id=?', (lesson,)).fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT content FROM notes WHERE id='note'").fetchone()[0], 'Keep this note')
            count = conn.execute('SELECT COUNT(*) FROM lessons WHERE course_id=?', (self.course_id,)).fetchone()[0]
            self.assertGreaterEqual(count, 24)
            course = conn.execute('SELECT * FROM courses WHERE id=?', (self.course_id,)).fetchone()
            self.assertEqual(course['lesson_count'], count)
            for row in conn.execute('SELECT source_citations FROM lessons WHERE course_id=?', (self.course_id,)):
                for citation in json.loads(row[0]):
                    self.assertIn(citation['text'], PAGES[citation['page']-1]['text'])

    def test_failed_commit_rolls_back_and_retry_resumes_same_segment(self):
        from app.services.segmented_generation import append_curriculum
        before = self.progress()
        def fail_after_append(conn, course_id, curriculum):
            append_curriculum(conn, course_id, curriculum)
            raise RuntimeError('Simulated storage interruption')
        with patch('app.routers.study.append_curriculum', side_effect=fail_after_append):
            response = self.owner.post(self.base+'/generate-next', json={'segment_index': 1})
            self.assertEqual(response.status_code, 500)
        self.assertEqual(self.progress(), before)
        response = self.owner.post(self.base+'/generate-next', json={'segment_index': 1})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['completed'], 2)

    def test_only_owner_can_continue_and_out_of_order_requests_are_rejected(self):
        for client, status in [(self.anon, 401), (self.other, 404)]:
            self.assertEqual(client.post(self.base+'/generate-next', json={'segment_index': 1}).status_code, status)
        self.assertEqual(self.owner.post(self.base+'/generate-next', json={'segment_index': 2}).status_code, 409)
        with closing(database.get_db_connection()) as conn, conn:
            conn.execute("UPDATE books SET visibility='public' WHERE id=?", (self.book_id,))
        self.assertEqual(self.other.post(self.base+'/generate-next', json={'segment_index': 1}).status_code, 404)
        self.assertEqual(self.progress()['completed'], 1)

    def test_trashing_during_provider_request_cannot_append_new_materials(self):
        from app.services.ai_analyzer import build_content_aware_curriculum
        async def trash_during_call(*args, **kwargs):
            with closing(database.get_db_connection()) as conn, conn:
                conn.execute('UPDATE books SET deleted_at=1 WHERE id=?', (self.book_id,))
            return build_content_aware_curriculum(*args, **{k:v for k,v in kwargs.items() if k not in {'lesson_target','previous_topics'}})
        with patch('app.routers.study.analyze_book_with_gemini', side_effect=trash_during_call):
            self.assertEqual(self.owner.post(self.base+'/generate-next', json={'segment_index': 1}).status_code, 404)
        with closing(database.get_db_connection()) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM generation_segments WHERE book_id=? AND status='completed'", (self.book_id,)).fetchone()[0], 1)
