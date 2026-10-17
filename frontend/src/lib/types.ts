export interface Book {
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
  prev_lesson?: { id: string; title: string; order_index: number } | null;
  next_lesson?: { id: string; title: string; order_index: number } | null;
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
  id: string;
  course_id: string;
  lesson_id?: string;
  question: string;
  answer: string;
  category: string;
  mastered: boolean;
}

export interface QuizQuestion {
  id: string;
  course_id: string;
  lesson_id?: string;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface Course {
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
