import { Book, Course, Lesson, Flashcard, QuizQuestion, QuizResult } from './types';
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export class ApiError extends Error {
    constructor(message: string, public status: number) { super(message); }
}
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    let response: Response;
    try {
        response = await fetch(`${API_BASE}${path}`, { cache: 'no-store', ...options, credentials: 'include' });
    }
    catch {
        throw new ApiError('Nu putem contacta serverul. Verifică dacă aplicația este pornită și încearcă din nou.', 0);
    }
    if (!response.ok) {
        let message = response.status === 401 ? 'Autentifică-te pentru a continua.' : response.status === 403 ? 'Nu ai acces la acest material.' : response.status === 404 ? 'Materialul solicitat nu a fost găsit.' : `Cererea nu a reușit (${response.status}).`;
        try {
            const body = await response.json();
            if (typeof body.detail === 'string')
                message = body.detail;
            else if (typeof body.detail?.message === 'string')
                message = body.detail.message;
            else if (Array.isArray(body.detail))
                message = body.detail.map((item: {
                    msg?: string;
                }) => item.msg || 'Date invalide.').join(' ');
        }
        catch { /* Preserve the HTTP error when no JSON exists. */ }
        throw new ApiError(message, response.status);
    }
    if (response.status === 204)
        return undefined as T;
    return response.json();
}
export function mutate<T>(path: string, body?: unknown, method = 'POST') {
    return request<T>(path, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
}
export function fetchBooks() { return request<Book[]>('/api/books'); }
export function fetchBook(id: string) { return request<Book>(`/api/books/${id}`); }
export interface UploadInput {
    file?: File;
    text?: string;
    title?: string;
    author?: string;
    language?: string;
    visibility?: string;
    study_minutes?: number;
    depth?: string;
    focus_keywords?: string;
}
export async function uploadBook(input: UploadInput | File, title?: string, author?: string) {
    const data = input instanceof File ? { file: input, title, author } : input;
    const form = new FormData();
    Object.entries(data).forEach(([key, value]) => { if (value !== undefined && value !== '')
        form.append(key, value instanceof File ? value : String(value)); });
    return request<{
        book_id: string;
        course_id?: string;
        title: string;
        language?: string;
        status?: string;
    }>('/api/books/upload', { method: 'POST', body: form });
}
export function fetchCourses(view = 'all', query = '') { return request<Course[]>(`/api/courses?view=${view}&q=${encodeURIComponent(query)}`); }
export function fetchCourse(id: string) { return request<Course>(`/api/courses/${id}`); }
export function fetchLesson(id: string, lang?: string) { return request<Lesson>(`/api/lessons/${id}${lang ? `?lang=${lang}` : ''}`); }
export function switchLessonLanguage(id: string, lang: string) { return mutate<Lesson>(`/api/lessons/${id}/language/${lang}`); }
export function toggleLessonComplete(id: string) { return mutate<{
    completed: boolean;
}>(`/api/lessons/${id}/complete`); }
export function saveLessonNotes(id: string, content: string) { return mutate<{
    status: string;
}>(`/api/lessons/${id}/notes`, { content }); }
export function fetchFlashcards(id: string) { return request<Flashcard[]>(`/api/flashcards/course/${id}`); }
export function toggleFlashcardMastery(id: string) { return mutate<{
    mastered: boolean;
}>(`/api/flashcards/${id}/master`); }
export function fetchQuizzes(id: string) { return request<QuizQuestion[]>(`/api/quizzes/course/${id}`); }
export function submitQuiz(id: string, answers: Record<string, number>) { return mutate<QuizResult>(`/api/quizzes/course/${id}/submit`, { answers }); }
export function generateLessonAudio(id: string, voice?: string, lang?: string, rate = '+0%') { return mutate<Lesson>(`/api/lessons/${id}/generate-audio`, { voice, lang, rate }); }
export function getLessonExportUrl(id: string, type: string, lang?: string) { return `${API_BASE}/api/export/lesson/${id}/${type}${lang ? `?lang=${lang}` : ''}`; }
export function getMediaUrl(url?: string) { return !url ? '' : /^https?:\/\//.test(url) ? url : `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`; }
export function getSystemHealth() { return request<{
    status: string;
}>('/api/demo/status'); }
export function resetDemoLibrary() { return mutate<void>('/api/demo/reset'); }
export async function downloadPdf(courseId: string, kind: string) {
    const response = await fetch(`${API_BASE}/api/study/${courseId}/pdf?kind=${kind}`, { credentials: 'include' });
    if (!response.ok)
        throw new ApiError('PDF-ul nu a putut fi exportat. Încearcă din nou.', response.status);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `4next-${kind}.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);
}
export function errorMessage(error: unknown) { return error instanceof Error ? error.message : 'A apărut o eroare. Încearcă din nou.'; }
