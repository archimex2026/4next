"""Consecutive bounded parts, committed with their materials; no detached worker or queue."""
import json
import math
import uuid


def plan_segments(pages, study_minutes):
    if len(pages) <= 24 and sum(len(p['text']) for p in pages) <= 75000:
        return []
    parts, spans, characters, page_numbers = [], [], 0, set()
    for page in pages:
        text, start = page['text'], 0
        while start < len(text) or not text and start == 0:
            if spans and (characters >= 12000 or len(page_numbers) >= 12 and page['page'] not in page_numbers):
                parts.append(spans)
                spans, characters, page_numbers = [], 0, set()
            end = min(len(text), start + 12000 - characters)
            if end < len(text):
                # Prefer a line boundary, preserving every character and code line.
                boundary = text.rfind('\n', start + (end-start)//2, end)
                if boundary > start:
                    end = boundary + 1
            spans.append({'page': page['page'], 'start': start, 'end': end})
            characters += end - start
            page_numbers.add(page['page'])
            start = end
            if not text:
                break
    if spans:
        parts.append(spans)
    return [{'segment_index': i, 'spans': spans, 'status': 'pending',
             'study_minutes': max(1, (i+1)*study_minutes//len(parts) - i*study_minutes//len(parts))}
            for i, spans in enumerate(parts)]


def segment_pages(segment, pages):
    by_page = {p['page']: p['text'] for p in pages}
    spans = segment['spans']
    if isinstance(spans, str):
        spans = json.loads(spans)
    return [{'page': s['page'], 'text': by_page[s['page']][s['start']:s['end']]} for s in spans]


def segment_target(segment):
    return min(4, max(1, math.ceil(segment['study_minutes'] / 5)))


def save_plan(conn, book_id, segments):
    conn.executemany('INSERT INTO generation_segments(book_id,segment_index,spans,study_minutes) VALUES(?,?,?,?)',
        [(book_id, s['segment_index'], json.dumps(s['spans']), s['study_minutes']) for s in segments])


def complete_segment(conn, book_id, index, curriculum, saved):
    conn.execute("""UPDATE generation_segments SET status='completed',generation_mode=?,cited_pages=?,lesson_count=?
        WHERE book_id=? AND segment_index=?""", (curriculum['generation_mode'], json.dumps(saved['cited_pages']), saved['lesson_count'], book_id, index))
    modes = {row[0] for row in conn.execute("SELECT generation_mode FROM generation_segments WHERE book_id=? AND status='completed'", (book_id,))}
    mode = next(iter(modes)) if len(modes) == 1 else 'mixed'
    conn.execute('UPDATE books SET generation_mode=? WHERE id=?', (mode, book_id))


def generation_progress(conn, book_id):
    rows = [dict(row) for row in conn.execute('SELECT * FROM generation_segments WHERE book_id=? ORDER BY segment_index', (book_id,))]
    if not rows:
        return None
    completed_pages, cited_pages, parts = set(), set(), []
    for row in rows:
        numbers = sorted({s['page'] for s in json.loads(row['spans'])})
        if row['status'] == 'completed':
            completed_pages.update(numbers)
        cited = json.loads(row['cited_pages'])
        cited_pages.update(cited)
        parts.append({'index': row['segment_index'], 'pages': numbers, 'status': row['status'],
            'generation_mode': row['generation_mode'], 'cited_pages': cited, 'lesson_count': row['lesson_count']})
    # A page split across parts is processed only once all of its spans have completed.
    pending_pages = {p for part in parts if part['status'] != 'completed' for p in part['pages']}
    completed_pages -= pending_pages
    return {'segments': parts, 'completed': sum(p['status'] == 'completed' for p in parts), 'total': len(parts),
        'processed_pages': sorted(completed_pages), 'cited_pages': sorted(cited_pages),
        'next_index': next((p['index'] for p in parts if p['status'] != 'completed'), None),
        'planned_minutes': sum(row['study_minutes'] for row in rows)}


def append_curriculum(conn, course_id, curriculum):
    """Append only; existing IDs, notes and progress survive continuation and retries."""
    def identity(text):
        return ' '.join(text.casefold().split())
    existing = {identity(row[0]) for row in conn.execute('SELECT long_explanation FROM lessons WHERE course_id=?', (course_id,))}
    level_number = conn.execute('SELECT COUNT(*) FROM levels WHERE course_id=?', (course_id,)).fetchone()[0]
    added, cited = 0, set()
    for level in curriculum['levels']:
        lessons = []
        for lesson in level['lessons']:
            key = identity(lesson['long_explanation'])
            if key not in existing:
                lessons.append(lesson)
                existing.add(key)
        if not lessons:
            continue
        level_number += 1
        level_id = 'lvl-' + uuid.uuid4().hex
        conn.execute('INSERT INTO levels(id,course_id,level_number,title,description) VALUES(?,?,?,?,?)',
            (level_id, course_id, level_number, level['title'], level['description']))
        for index, lesson in enumerate(lessons):
            conn.execute('''INSERT INTO lessons(id,course_id,level_id,order_index,title,short_summary,long_explanation,
                key_ideas,practical_insights,examples,action_items,mermaid_diagram,duration,source_citations,transcript)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                ('lsn-' + uuid.uuid4().hex, course_id, level_id, index+1, lesson['title'], lesson['short_summary'], lesson['long_explanation'],
                 *[json.dumps(lesson.get(field, []), ensure_ascii=False) for field in ('key_ideas','practical_insights','examples','action_items')],
                 '', lesson.get('duration') or '5 min', json.dumps(lesson['source_citations'], ensure_ascii=False), '[]'))
            added += 1
            cited.update(c['page'] for c in lesson['source_citations'])
    for table, prefix, fields in [('flashcards', 'fc-', ('question','answer','category')),
                                  ('quizzes', 'qz-', ('question','options','correct_index','explanation'))]:
        questions = {identity(row[0]) for row in conn.execute(f'SELECT question FROM {table} WHERE course_id=?', (course_id,))}
        for item in curriculum[table]:
            key = identity(item['question'])
            if key in questions:
                continue
            questions.add(key)
            values = [json.dumps(item[field], ensure_ascii=False) if field == 'options' else item[field] for field in fields]
            columns = ','.join(('id','course_id',*fields,'source_citations'))
            marks = ','.join('?' for _ in range(len(fields)+3))
            conn.execute(f'INSERT INTO {table}({columns}) VALUES({marks})',
                (prefix + uuid.uuid4().hex, course_id, *values, json.dumps(item['source_citations'], ensure_ascii=False)))
    conn.execute('''UPDATE courses SET level_count=(SELECT COUNT(*) FROM levels WHERE course_id=?),
        lesson_count=(SELECT COUNT(*) FROM lessons WHERE course_id=?), quiz_count=(SELECT COUNT(*) FROM quizzes WHERE course_id=?),
        flashcard_count=(SELECT COUNT(*) FROM flashcards WHERE course_id=?) WHERE id=?''', (course_id,)*5)
    return {'lesson_count': added, 'cited_pages': sorted(cited)}
