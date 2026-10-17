import { Book, Course, Lesson, Flashcard, QuizQuestion, QuizResult } from './types';
import { DEMO_COURSE, DEMO_QUIZZES } from './demoData';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchBooks(): Promise<Book[]> {
  try {
    const res = await fetch(`${API_BASE}/api/books`, { cache: 'no-store' });
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }
  return [DEMO_COURSE.book as Book];
}

export async function fetchBook(id: string): Promise<Book> {
  try {
    const res = await fetch(`${API_BASE}/api/books/${id}`, { cache: 'no-store' });
    if (res.ok) return await res.json();
    if (res.status === 404 && id === 'book-lean-startup') {
      return DEMO_COURSE.book as Book;
    }
  } catch (err) {
    if (id === 'book-lean-startup') {
      return DEMO_COURSE.book as Book;
    }
    console.error(`Error fetching book ${id}:`, err);
  }
  
  if (id === 'book-lean-startup') {
    return DEMO_COURSE.book as Book;
  }
  return {
    id,
    title: 'Analyzing Document...',
    author: 'Author',
    page_count: 1,
    cover_color: '#0A66C2',
    status: 'processing',
    course_id: undefined,
  };
}

export async function uploadBook(
  input: { file?: File; text?: string; title?: string; author?: string; language?: string } | File,
  legacyTitle?: string,
  legacyAuthor?: string
): Promise<{ book_id: string; title: string; language?: string; course_id?: string; status?: string }> {
  const formData = new FormData();

  if (input instanceof File) {
    formData.append('file', input);
    if (legacyTitle) formData.append('title', legacyTitle);
    if (legacyAuthor) formData.append('author', legacyAuthor);
    formData.append('language', 'ro');
  } else {
    if (input.file) formData.append('file', input.file);
    if (input.text) formData.append('text', input.text);
    if (input.title) formData.append('title', input.title);
    if (input.author) formData.append('author', input.author);
    formData.append('language', input.language || 'ro');
  }

  const res = await fetch(`${API_BASE}/api/books/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    let errorDetail = `Upload failed with HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) errorDetail = errJson.detail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return await res.json();
}

export async function fetchCourses(): Promise<Course[]> {
  try {
    const res = await fetch(`${API_BASE}/api/courses`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) return data;
    }
  } catch (err) {
    console.error('Error fetching courses:', err);
  }
  return [DEMO_COURSE];
}

export async function fetchCourse(id: string): Promise<Course> {
  try {
    const res = await fetch(`${API_BASE}/api/courses/${id}`, { cache: 'no-store' });
    if (res.ok) return await res.json();
  } catch {
    // Backend offline fallback
  }
  return DEMO_COURSE;
}

export async function fetchLesson(id: string, lang: 'ro' | 'en' = 'ro'): Promise<Lesson> {
  try {
    const res = await fetch(`${API_BASE}/api/lessons/${id}?lang=${lang}`, { cache: 'no-store' });
    if (res.ok) return await res.json();
  } catch {
    // Backend offline fallback
  }
  const allLessons = DEMO_COURSE.levels?.flatMap((lvl) => lvl.lessons) || [];
  const found = allLessons.find((l) => l.id === id) || allLessons[0];
  if (found) {
    return {
      ...found,
      active_audio_url: lang === 'en' ? (found.audio_url_en || found.audio_url) : (found.audio_url_ro || found.audio_url),
      active_transcript: lang === 'en' ? (found.transcript_en || found.transcript) : (found.transcript_ro || found.transcript),
    };
  }
  throw new Error(`Lesson ${id} not found`);
}

export async function switchLessonLanguage(id: string, lang: 'ro' | 'en'): Promise<Lesson> {
  try {
    const res = await fetch(`${API_BASE}/api/lessons/${id}/language/${lang}`, { method: 'POST' });
    if (res.ok) return await res.json();
  } catch {
    // Backend offline fallback
  }
  return fetchLesson(id, lang);
}

export function getLessonExportUrl(lessonId: string, type: 'audio' | 'video' | 'diagram' | 'text', lang: 'ro' | 'en' = 'ro'): string {
  if (type === 'audio') return `${API_BASE}/api/export/lesson/${lessonId}/audio?lang=${lang}`;
  if (type === 'video') return `${API_BASE}/api/export/lesson/${lessonId}/video`;
  if (type === 'diagram') return `${API_BASE}/api/export/lesson/${lessonId}/diagram`;
  if (type === 'text') return `${API_BASE}/api/export/lesson/${lessonId}/text`;
  return `${API_BASE}/api/export/course/${lessonId}/markdown`;
}

export async function toggleLessonComplete(id: string): Promise<{ completed: boolean }> {
  try {
    const res = await fetch(`${API_BASE}/api/lessons/${id}/complete`, { method: 'POST' });
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }
  return { completed: true };
}

export async function saveLessonNotes(id: string, content: string): Promise<{ status: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/lessons/${id}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }
  return { status: 'saved' };
}

export async function fetchFlashcards(courseId: string): Promise<Flashcard[]> {
  try {
    const res = await fetch(`${API_BASE}/api/flashcards/course/${courseId}`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) return data;
    }
  } catch {
    // Backend offline fallback
  }
  return DEMO_COURSE.flashcards || [];
}

export async function toggleFlashcardMastery(cardId: string): Promise<{ mastered: boolean }> {
  try {
    const res = await fetch(`${API_BASE}/api/flashcards/${cardId}/master`, { method: 'POST' });
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }
  return { mastered: true };
}

export async function fetchQuizzes(courseId: string): Promise<QuizQuestion[]> {
  try {
    const res = await fetch(`${API_BASE}/api/quizzes/course/${courseId}`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) return data;
    }
  } catch {
    // Backend offline fallback
  }
  return DEMO_QUIZZES;
}

export async function submitQuiz(courseId: string, answers: Record<string, number>): Promise<QuizResult> {
  try {
    const res = await fetch(`${API_BASE}/api/quizzes/course/${courseId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers }),
    });
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }

  let score = 0;
  const feedback = DEMO_QUIZZES.map((q) => {
    const userSelected = answers[q.id];
    const isCorrect = userSelected === q.correct_index;
    if (isCorrect) score += 1;
    return {
      quiz_id: q.id,
      question: q.question,
      options: q.options,
      selected_index: userSelected !== undefined ? userSelected : -1,
      correct_index: q.correct_index,
      is_correct: isCorrect,
      explanation: q.explanation || '',
    };
  });

  const percentage = Math.round((score / DEMO_QUIZZES.length) * 100);
  return {
    score,
    total: DEMO_QUIZZES.length,
    percentage,
    passed: percentage >= 70,
    feedback,
  };
}

export async function resetDemoLibrary(): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/demo/reset`, { method: 'POST' });
  } catch {
    // Fallback
  }
}

export async function getSystemHealth(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/demo/status`, { cache: 'no-store' });
    if (res.ok) return await res.json();
  } catch {
    return { status: 'fallback_ready' };
  }
}

export async function generateLessonAudio(
  lessonId: string, 
  voice: string = 'ro-RO-AlinaNeural', 
  lang: 'ro' | 'en' = 'ro',
  rate: string = '+0%'
): Promise<Lesson> {
  const res = await fetch(`${API_BASE}/api/lessons/${lessonId}/generate-audio`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ voice, lang, rate }),
  });
  if (!res.ok) {
    throw new Error(`Failed to generate neural audio: ${res.statusText}`);
  }
  return await res.json();
}

export function getMediaUrl(relativeOrAbsoluteUrl?: string): string {
  if (!relativeOrAbsoluteUrl) return '';
  if (relativeOrAbsoluteUrl.startsWith('http')) return relativeOrAbsoluteUrl;
  return `${API_BASE}${relativeOrAbsoluteUrl.startsWith('/') ? '' : '/'}${relativeOrAbsoluteUrl}`;
}


