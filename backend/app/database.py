import sqlite3
import json
from typing import Any, List, Dict, Optional
from app.config import DB_PATH

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
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
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        except sqlite3.OperationalError:
            pass # Column already exists

    safe_add_column("books", "language TEXT DEFAULT 'en'")
    safe_add_column("courses", "language TEXT DEFAULT 'en'")
    safe_add_column("lessons", "audio_url_ro TEXT")
    safe_add_column("lessons", "audio_url_en TEXT")
    safe_add_column("lessons", "transcript_ro TEXT")
    safe_add_column("lessons", "transcript_en TEXT")

    conn.commit()
    conn.close()
