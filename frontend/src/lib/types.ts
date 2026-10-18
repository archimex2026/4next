export interface Book {
    language?: string;
    visibility?: 'private' | 'public';
    owner_id?: string;
    id: string;
    title: string;
    author: string;
    page_count: number;
    file_path?: string;
    file_name?: string;
    file_type?: string;
    file_size?: number;
    cover_color?: string;
    status: 'processing' | 'analyzing' | 'ready' | 'failed';
    summary?: string;
    created_at?: string;
    course_id?: string;
}
export interface Lesson {
    source_citations?: Citation[];
    id: string;
    course_id: string;
    level_id: string;
    order_index: number;
    title: string;
    short_summary: string;
    long_explanation: string;
    key_ideas: string[];
    practical_insights: string[];
    examples: string[];
    action_items: string[];
    mermaid_diagram: string;
    audio_url?: string;
    audio_url_ro?: string;
    audio_url_en?: string;
    active_audio_url?: string;
    video_url?: string;
    transcript: {
        scene: number;
        title: string;
        timestamp: string;
        speaker: string;
    }[];
    transcript_ro?: {
        scene: number;
        title: string;
        timestamp: string;
        speaker: string;
    }[];
    transcript_en?: {
        scene: number;
        title: string;
        timestamp: string;
        speaker: string;
    }[];
    active_transcript?: {
        scene: number;
        title: string;
        timestamp: string;
        speaker: string;
    }[];
    duration: string;
    completed: boolean;
    notes?: string;
    prev_lesson?: {
        id: string;
        title: string;
        order_index: number;
    } | null;
    next_lesson?: {
        id: string;
        title: string;
        order_index: number;
    } | null;
}
export interface Level {
    id: string;
    course_id: string;
    level_number: number;
    title: string;
    description: string;
    lessons: Lesson[];
}
export interface Flashcard {
    source_citations?: Citation[];
    id: string;
    course_id: string;
    lesson_id?: string;
    question: string;
    answer: string;
    category: string;
    mastered: boolean;
}
export interface QuizQuestion {
    source_citations?: Citation[];
    id: string;
    course_id: string;
    lesson_id?: string;
    question: string;
    options: string[];
    correct_index: number;
    explanation: string;
}
export interface Course {
  keywords?: string[];
    shared_by?: string;
    owner_id?: string;
    is_owner?: boolean;
    visibility?: 'private' | 'public';
    language?: string;
    rating_average?: number;
    rating_count?: number;
    id: string;
    book_id: string;
    title: string;
    subtitle?: string;
    overview: string;
    target_audience?: string;
    estimated_duration: string;
    level_count: number;
    lesson_count: number;
    quiz_count: number;
    flashcard_count: number;
    completion_percentage?: number;
    book_title?: string;
    author?: string;
    cover_color?: string;
    page_count?: number;
    created_at?: string;
    levels?: Level[];
    flashcards?: Flashcard[];
    quizzes?: QuizQuestion[];
    book?: Book;
}
export interface QuizResult {
    score: number;
    total: number;
    percentage: number;
    passed: boolean;
    feedback: {
        quiz_id: string;
        question: string;
        options: string[];
        selected_index: number;
        correct_index: number;
        is_correct: boolean;
        explanation: string;
    }[];
}
export interface User {
    id: string;
    name: string;
    email: string;
    study_minutes: number;
    depth: string;
    exam_goal?: string;
}
export interface SourcePage {
    page: number;
    text: string;
}
export interface StudySource {
    generation_progress?: GenerationProgress | null;
    title: string;
    language: string;
    pages: SourcePage[];
    page_kind?: string;
    keywords: string[];
    focus_keywords?: string[];
    study_minutes: number;
    depth: string;
    generation_mode: string;
}
export interface GenerationProgress {
    completed: number;
    total: number;
    processed_pages: number[];
    cited_pages: number[];
    next_index: number | null;
    planned_minutes: number;
    segments: {
        index: number;
        pages: number[];
        status: 'pending' | 'completed';
        generation_mode: string | null;
        cited_pages: number[];
        lesson_count: number;
    }[];
}
export interface Highlight {
    id: string;
    page: number;
    start_offset: number;
    end_offset: number;
    text: string;
    color: string;
}
export interface Citation {
    page: number;
    text: string;
    source_title: string;
}
export interface ChatAnswer {
    answer: string;
    citations: Citation[];
    mode: string;
    related_concepts: string[];
}
export interface Suggestions {
    concepts: {
        term: string;
        query: string;
        reason: string;
    }[];
    courses: Course[];
    google_query?: string;
    google_url?: string;
}
export interface StudyGroup {
    id: string;
    name: string;
    subject: string;
    invite_code?: string;
    member_count?: number;
    material_count?: number;
    owner_id?: string;
    members?: {
        id: string;
        name: string;
    }[];
    courses?: Course[];
}
export interface TrashedCourse {
    id: string;
    book_id: string;
    title: string;
    description: string;
    deleted_at: string;
    purge_at: string;
    language?: string;
}
