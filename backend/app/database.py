import sqlite3
import json
from typing import Any, List, Dict, Optional
from app.config import DB_PATH

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Books table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT,
        page_count INTEGER DEFAULT 0,
        file_path TEXT,
        file_name TEXT,
        file_type TEXT,
        file_size INTEGER DEFAULT 0,
        cover_color TEXT DEFAULT '#0A66C2',
        status TEXT DEFAULT 'ready',
        summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Courses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id TEXT PRIMARY KEY,
        book_id TEXT NOT NULL,
        title TEXT NOT NULL,
        subtitle TEXT,
        overview TEXT,
        target_audience TEXT,
        estimated_duration TEXT DEFAULT '15 mins',
        level_count INTEGER DEFAULT 3,
        lesson_count INTEGER DEFAULT 6,
        quiz_count INTEGER DEFAULT 6,
        flashcard_count INTEGER DEFAULT 12,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
    )
    """)

    # Levels table (Curriculum Roadmap)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS levels (
        id TEXT PRIMARY KEY,
        course_id TEXT NOT NULL,
        level_number INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    )
    """)

    # Lessons table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lessons (
        id TEXT PRIMARY KEY,
        course_id TEXT NOT NULL,
        level_id TEXT NOT NULL,
        order_index INTEGER NOT NULL,
        title TEXT NOT NULL,
        short_summary TEXT,
        long_explanation TEXT,
        key_ideas TEXT,          -- JSON list
        practical_insights TEXT, -- JSON list
        examples TEXT,           -- JSON list
        action_items TEXT,       -- JSON list
        mermaid_diagram TEXT,
        audio_url TEXT,
        video_url TEXT,
        transcript TEXT,         -- JSON scenes list
        duration TEXT DEFAULT '2 mins',
        completed BOOLEAN DEFAULT 0,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
        FOREIGN KEY (level_id) REFERENCES levels (id) ON DELETE CASCADE
    )
    """)

    # Flashcards table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flashcards (
        id TEXT PRIMARY KEY,
        course_id TEXT NOT NULL,
        lesson_id TEXT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        category TEXT DEFAULT 'Key Concept',
        mastered BOOLEAN DEFAULT 0,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    )
    """)

    # Quizzes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id TEXT PRIMARY KEY,
        course_id TEXT NOT NULL,
        lesson_id TEXT,
        question TEXT NOT NULL,
        options TEXT NOT NULL,       -- JSON list of strings
        correct_index INTEGER NOT NULL,
        explanation TEXT,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    )
    """)

    # Course Progress / User Notes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        course_id TEXT NOT NULL,
        lesson_id TEXT NOT NULL,
        content TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Run automatic migrations for schema enhancements
    def safe_add_column(table: str, column_def: str):
        columns = {row[1] for row in cursor.execute(f"PRAGMA table_info({table})")}
        if column_def.split()[0] not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

    legacy_books = "visibility" not in {row[1] for row in cursor.execute("PRAGMA table_info(books)")}
    safe_add_column("books", "language TEXT DEFAULT 'en'")
    for column in (
        "owner_id TEXT", "visibility TEXT NOT NULL DEFAULT 'private'", "source_text TEXT DEFAULT ''",
        "source_pages TEXT DEFAULT '[]'", "keywords TEXT DEFAULT '[]'", "focus_keywords TEXT DEFAULT '[]'", "study_minutes INTEGER DEFAULT 20",
        "depth TEXT DEFAULT 'standard'", "generation_mode TEXT DEFAULT 'extractive'", "deleted_at INTEGER",
    ):
        safe_add_column("books", column)
    if legacy_books:
        # Only known bundled samples are public; unassigned legacy uploads stay private.
        cursor.execute("""UPDATE books SET visibility = 'public' WHERE owner_id IS NULL
            AND id IN ('book-lean-startup','book-atomic-habits')""")
    safe_add_column("courses", "language TEXT DEFAULT 'en'")
    safe_add_column("notes", "user_id TEXT")
    safe_add_column("lessons", "audio_url_ro TEXT")
    safe_add_column("lessons", "audio_url_en TEXT")
    safe_add_column("lessons", "transcript_ro TEXT")
    safe_add_column("lessons", "transcript_en TEXT")
    for table in ("lessons", "flashcards", "quizzes"):
        safe_add_column(table, "source_citations TEXT DEFAULT '[]'")

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL, study_minutes INTEGER NOT NULL DEFAULT 20,
        depth TEXT NOT NULL DEFAULT 'standard', exam_goal TEXT NOT NULL DEFAULT '',
        terms_accepted_at TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS auth_attempts (
        key TEXT PRIMARY KEY, attempts INTEGER NOT NULL DEFAULT 0, window_start INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS generation_usage (
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, operation TEXT NOT NULL,
        period INTEGER NOT NULL, bucket INTEGER NOT NULL, requests INTEGER NOT NULL,
        PRIMARY KEY(user_id, operation, period, bucket)
    );
    CREATE TABLE IF NOT EXISTS ratings (
        book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        stars INTEGER NOT NULL CHECK(stars BETWEEN 1 AND 5),
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(book_id, user_id)
    );
    CREATE TABLE IF NOT EXISTS study_groups (
        id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id),
        name TEXT NOT NULL, subject TEXT NOT NULL DEFAULT '', invite_code TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS group_members (
        group_id TEXT NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(group_id, user_id)
    );
    CREATE TABLE IF NOT EXISTS group_materials (
        group_id TEXT NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
        course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        shared_by TEXT NOT NULL REFERENCES users(id),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(group_id, course_id)
    );
    CREATE TABLE IF NOT EXISTS user_lesson_progress (
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id TEXT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
        completed INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, lesson_id)
    );
    CREATE TABLE IF NOT EXISTS user_flashcard_progress (
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        card_id TEXT NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
        mastered INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, card_id)
    );
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        score INTEGER NOT NULL, total INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS highlights (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        page INTEGER NOT NULL, start_offset INTEGER NOT NULL, end_offset INTEGER NOT NULL,
        text TEXT NOT NULL, color TEXT NOT NULL DEFAULT 'yellow', created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_books_owner ON books(owner_id);
    CREATE INDEX IF NOT EXISTS idx_books_deleted_at ON books(deleted_at);
    CREATE TABLE IF NOT EXISTS trash_file_cleanup (
        kind TEXT NOT NULL, name TEXT NOT NULL, PRIMARY KEY(kind,name)
    );
    CREATE INDEX IF NOT EXISTS idx_courses_book ON courses(book_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
    CREATE INDEX IF NOT EXISTS idx_notes_user_lesson ON notes(user_id, lesson_id);
    CREATE INDEX IF NOT EXISTS idx_group_material_course ON group_materials(course_id);
    """)

    conn.commit()
    conn.close()
