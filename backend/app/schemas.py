from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class BookBase(BaseModel):
    id: str
    title: str
    author: Optional[str] = "Unknown Author"
    page_count: int = 0
    file_type: str = "pdf"
    file_name: Optional[str] = None
    file_size: int = 0
    cover_color: str = "#0A66C2"
    status: str = "ready"
    summary: Optional[str] = None
    created_at: Optional[str] = None

class FlashcardSchema(BaseModel):
    id: str
    course_id: str
    lesson_id: Optional[str] = None
    question: str
    answer: str
    category: str = "Key Concept"
    mastered: bool = False

class QuizQuestionSchema(BaseModel):
    id: str
    course_id: str
    lesson_id: Optional[str] = None
    question: str
    options: List[str]
    correct_index: int
    explanation: str

class LessonSchema(BaseModel):
    id: str
    course_id: str
    level_id: str
    order_index: int
    title: str
    short_summary: str
    long_explanation: str
    key_ideas: List[str]
    practical_insights: List[str]
    examples: List[str]
    action_items: List[str]
    mermaid_diagram: str
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    transcript: List[Dict[str, Any]] = []
    duration: str = "2 mins"
    completed: bool = False

class LevelSchema(BaseModel):
    id: str
    course_id: str
    level_number: int
    title: str
    description: str
    lessons: List[LessonSchema] = []

class CourseDetailSchema(BaseModel):
    id: str
    book_id: str
    title: str
    subtitle: Optional[str] = None
    overview: str
    target_audience: Optional[str] = None
    estimated_duration: str = "15 mins"
    level_count: int = 3
    lesson_count: int = 6
    quiz_count: int = 6
    flashcard_count: int = 12
    levels: List[LevelSchema] = []
    flashcards: List[FlashcardSchema] = []
    quizzes: List[QuizQuestionSchema] = []
    book: Optional[BookBase] = None

class QuizSubmissionSchema(BaseModel):
    answers: Dict[str, int] # quiz_id -> selected_index

class QuizResultSchema(BaseModel):
    score: int
    total: int
    percentage: float
    passed: bool
    feedback: List[Dict[str, Any]]

class NoteUpdateSchema(BaseModel):
    content: str

class GenerateAudioRequest(BaseModel):
    voice: Optional[str] = "ro-RO-AlinaNeural"
    lang: Optional[str] = "ro"
    rate: Optional[str] = "+0%"
    custom_script: Optional[str] = None

