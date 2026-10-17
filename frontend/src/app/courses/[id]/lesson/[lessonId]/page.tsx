'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  Play, CheckCircle2, ArrowLeft, ArrowRight, 
  Video, Headphones, Layers, Award, Save, Check,
  ChevronLeft, ChevronRight, FileText, Sparkles,
  BookOpen, Clock, Download, Copy, CheckCheck,
  ShieldCheck, RefreshCw, Mic, ExternalLink
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { fetchLesson, fetchCourse, toggleLessonComplete, saveLessonNotes, getLessonExportUrl } from '@/lib/api';
import { Lesson, Course } from '@/lib/types';
import AudioPlayer from '@/components/AudioPlayer';
import MermaidDiagram from '@/components/MermaidDiagram';

function ClassroomContent() {
  const params = useParams();
  const router = useRouter();
  const courseId = params?.id as string;
  const lessonId = params?.lessonId as string;

  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [selectedLang, setSelectedLang] = useState<'ro' | 'en'>('ro');

  // Notes state
  const [notes, setNotes] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  const [noteSavedFeedback, setNoteSavedFeedback] = useState(false);

  // Right sidebar tab: 'syllabus' | 'notes' | 'flashcards'
  const [rightTab, setRightTab] = useState<'syllabus' | 'notes' | 'flashcards'>('syllabus');

  // Flashcard quick widget state
  const [fcFlipped, setFcFlipped] = useState(false);
  const [fcIndex, setFcIndex] = useState(0);

  // Copy diagram state
  const [copiedCode, setCopiedCode] = useState(false);

  useEffect(() => {
    if (!lessonId || !courseId) return;
    setLoading(true);

    Promise.all([
      fetchLesson(lessonId, selectedLang),
      fetchCourse(courseId)
    ])
      .then(([lessonData, courseData]) => {
        setLesson(lessonData);
        setCourse(courseData);
        setCompleted(lessonData.completed);
        setNotes(lessonData.notes || '');
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [lessonId, courseId]);

  const handleLanguageChange = async (newLang: 'ro' | 'en') => {
    if (!lesson) return;
    setSelectedLang(newLang);
    try {
      const updated = await fetchLesson(lesson.id, newLang);
      setLesson(updated);
    } catch (e) {
      console.error('Error changing audio language:', e);
    }
  };

  const handleToggleComplete = async () => {
    if (!lesson) return;
    try {
      const res = await toggleLessonComplete(lesson.id);
      setCompleted(res.completed);
      if (res.completed) {
        confetti({ particleCount: 80, spread: 60, origin: { y: 0.7 } });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveNotes = async () => {
    if (!lesson) return;
    setSavingNotes(true);
    try {
      await saveLessonNotes(lesson.id, notes);
      setNoteSavedFeedback(true);
      setTimeout(() => setNoteSavedFeedback(false), 2000);
    } catch (e) {
      console.error(e);
    } finally {
      setSavingNotes(false);
    }
  };

  const handleCopyDiagram = () => {
    if (!lesson?.mermaid_diagram) return;
    navigator.clipboard.writeText(lesson.mermaid_diagram);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  if (loading || !lesson || !course) {
    return (
      <div className="max-w-[1200px] mx-auto px-4 py-8">
        <div className="h-[500px] bg-white rounded-lg border border-[#DFE3D9] animate-pulse" />
      </div>
    );
  }

  const allLessons = course.levels?.flatMap((lvl) => lvl.lessons) || [];
  const currentIdx = allLessons.findIndex((l) => l.id === lesson.id);
  const nextLesson = allLessons[currentIdx + 1] || null;
  const prevLesson = allLessons[currentIdx - 1] || null;
  const completedCount = allLessons.filter((l) => l.completed).length;
  const courseProgressPercent = allLessons.length > 0 ? Math.round((completedCount / allLessons.length) * 100) : 33;

  const lessonFlashcards = course.flashcards?.filter((f) => f.lesson_id === lesson.id) || course.flashcards || [];
  const activeCard = lessonFlashcards[fcIndex] || {
    question: `Care este invariantul fundamental din ${lesson.title}?`,
    answer: lesson.short_summary
  };

  const activeAudio = selectedLang === 'ro' 
    ? (lesson.audio_url_ro || lesson.active_audio_url || lesson.audio_url)
    : (lesson.audio_url_en || lesson.active_audio_url || lesson.audio_url);

  return (
    <div className="min-h-screen bg-[#F8F7F2] text-[#25382F] pb-16">
      
      {/* LinkedIn Enterprise Subheader Bar */}
      <div className="bg-white border-b border-[#DFE3D9] px-4 py-3 sticky top-[56px] z-40 shadow-xs">
        <div className="max-w-[1200px] mx-auto flex flex-wrap items-center justify-between gap-3">
          
          {/* Breadcrumb / Title */}
          <div className="flex items-center gap-3 truncate">
            <Link
              href={`/courses/${course.id}`}
              className="p-1.5 rounded-full hover:bg-[#F8F7F2] text-[#68736B] hover:text-[#25382F] transition-colors"
              title="Înapoi la structura cursului"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="truncate">
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-[#315D50] font-semibold uppercase tracking-wider">
                  {course.title}
                </span>
                <span className="text-[#68736B] text-xs">•</span>
                <span className="text-xs text-[#68736B]">
                  Lecția {lesson.order_index} din {allLessons.length}
                </span>
              </div>
              <h1 className="text-sm sm:text-base font-bold text-[#25382F] truncate">
                {lesson.title}
              </h1>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {/* Bilingual Switcher */}
            <div className="flex items-center border border-[#DFE3D9] rounded-full p-0.5 bg-[#F8F7F2] text-xs font-semibold">
              <button
                type="button"
                onClick={() => handleLanguageChange('ro')}
                className={`px-2.5 py-1 rounded-full transition-all ${
                  selectedLang === 'ro'
                    ? 'bg-white text-[#315D50] shadow-xs'
                    : 'text-[#68736B] hover:text-[#25382F]'
                }`}
              >
                🇷🇴 Română
              </button>
              <button
                type="button"
                onClick={() => handleLanguageChange('en')}
                className={`px-2.5 py-1 rounded-full transition-all ${
                  selectedLang === 'en'
                    ? 'bg-white text-[#315D50] shadow-xs'
                    : 'text-[#68736B] hover:text-[#25382F]'
                }`}
              >
                🇬🇧 English
              </button>
            </div>

            {/* Video Mode Switch */}
            <Link
              href={`/courses/${course.id}/video/${lesson.id}`}
              className="px-3.5 py-1.5 rounded-full border border-[#DFE3D9] hover:border-[#315D50] bg-white text-[#25382F] text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <Video className="w-3.5 h-3.5 text-[#315D50]" />
              <span className="hidden sm:inline">Mod Video Tutorial</span>
            </Link>

            {/* Complete Lesson Button */}
            <button
              onClick={handleToggleComplete}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-xs ${
                completed
                  ? 'bg-[#3E6650] text-white'
                  : 'bg-[#315D50] hover:bg-[#23473C] text-white'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{completed ? 'Finalizat ✓' : 'Marchează Finalizat'}</span>
            </button>
          </div>

        </div>
      </div>

      {/* Main Classroom Layout */}
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Main Column (8 cols): Audio Player & Lesson Substance */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Enterprise Neural Audio Player */}
            <AudioPlayer
              audioUrl={activeAudio}
              title={`${lesson.title} - Narațiune Audio Didactică`}
              lessonId={lesson.id}
              lessonNumber={lesson.order_index}
              currentLang={selectedLang}
              onLanguageChange={handleLanguageChange}
              onAudioRegenerated={(newUrl, dur) => {
                setLesson((prev) => prev ? { ...prev, active_audio_url: newUrl, audio_url_ro: newUrl } : null);
              }}
            />

            {/* Theoretical Foundation Card */}
            <div className="bg-white border border-[#DFE3D9] rounded-lg p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-[#ECEEE7]">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#315D50]" />
                  <h2 className="text-sm font-bold text-[#25382F] uppercase tracking-wide">
                    Ideile pe înțelesul tău
                  </h2>
                </div>
                <span className="text-xs text-[#68736B]">
                  Durată: {lesson.duration || '2 mins'}
                </span>
              </div>

              <div className="p-3 bg-[#EDF2E9] border border-[#315D50]/20 rounded-md">
                <p className="text-xs sm:text-sm font-semibold text-[#315D50] leading-relaxed">
                  💡 {lesson.short_summary}
                </p>
              </div>

              {lesson.long_explanation && (
                <div className="text-xs sm:text-sm text-[#25382F] leading-relaxed space-y-2 pt-1">
                  <p>{lesson.long_explanation}</p>
                </div>
              )}
            </div>

            {/* Key Ideas & Invariant Rules Card */}
            {lesson.key_ideas && lesson.key_ideas.length > 0 && (
              <div className="bg-white border border-[#DFE3D9] rounded-lg p-5 shadow-xs space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-[#ECEEE7]">
                  <CheckCircle2 className="w-4 h-4 text-[#3E6650]" />
                  <h3 className="text-sm font-bold text-[#25382F] uppercase tracking-wide">
                    Reguli Invariante & Principii Cheie
                  </h3>
                </div>

                <div className="space-y-2">
                  {lesson.key_ideas.map((idea, i) => (
                    <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-md bg-[#FAFAFA] border border-[#DFE3D9]">
                      <span className="w-5 h-5 rounded-full bg-[#EDF2E9] text-[#315D50] font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      <p className="text-xs sm:text-sm font-medium text-[#25382F] leading-normal">
                        {idea}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* UML Architecture Diagram Card */}
            {lesson.mermaid_diagram && (
              <div className="bg-white border border-[#DFE3D9] rounded-lg p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-[#ECEEE7]">
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-[#315D50]" />
                    <h3 className="text-sm font-bold text-[#25382F] uppercase tracking-wide">
                      Model Arhitectural & Diagramă Vizuală
                    </h3>
                  </div>
                  <button
                    onClick={handleCopyDiagram}
                    className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full border border-[#DFE3D9] hover:bg-[#F8F7F2] text-[#68736B] hover:text-[#25382F] transition-colors"
                  >
                    {copiedCode ? <CheckCheck className="w-3.5 h-3.5 text-[#3E6650]" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedCode ? 'Copiat' : 'Copiază Mermaid'}</span>
                  </button>
                </div>

                <div className="p-4 bg-[#FAFAFA] border border-[#DFE3D9] rounded-lg overflow-x-auto">
                  <MermaidDiagram chart={lesson.mermaid_diagram} />
                </div>
              </div>
            )}

            {/* Real World Practical Application */}
            {lesson.examples && lesson.examples.length > 0 && (
              <div className="bg-white border border-[#DFE3D9] rounded-lg p-5 shadow-xs space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-[#ECEEE7]">
                  <BookOpen className="w-4 h-4 text-[#7C3AED]" />
                  <h3 className="text-sm font-bold text-[#25382F] uppercase tracking-wide">
                    Studiu de Caz & Aplicabilitate Practică
                  </h3>
                </div>

                <div className="space-y-2">
                  {lesson.examples.map((ex, i) => (
                    <div key={i} className="p-3 rounded-md bg-[#FAF5FF] border border-[#7C3AED]/20">
                      <p className="text-xs sm:text-sm text-[#25382F] leading-relaxed">
                        <strong className="text-[#7C3AED]">Exemplul {i + 1}:</strong> {ex}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Items Checklist */}
            {lesson.action_items && lesson.action_items.length > 0 && (
              <div className="bg-white border border-[#DFE3D9] rounded-lg p-5 shadow-xs space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-[#ECEEE7]">
                  <Check className="w-4 h-4 text-[#3E6650]" />
                  <h3 className="text-sm font-bold text-[#25382F] uppercase tracking-wide">
                    Plan de Acțiune Imediată
                  </h3>
                </div>

                <div className="space-y-2">
                  {lesson.action_items.map((action, i) => (
                    <div key={i} className="flex items-center gap-2.5 p-2.5 rounded-md bg-[#E8EFE4]/50 border border-[#3E6650]/20">
                      <span className="w-4 h-4 rounded-full bg-[#3E6650] text-white flex items-center justify-center text-[10px] shrink-0 font-bold">
                        ✓
                      </span>
                      <span className="text-xs sm:text-sm font-medium text-[#25382F]">
                        {action}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Navigation Bottom Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-[#DFE3D9]">
              {prevLesson ? (
                <Link
                  href={`/courses/${course.id}/lesson/${prevLesson.id}`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-[#315D50] text-[#315D50] hover:bg-[#EDF2E9] text-xs font-semibold transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Lecția Precedentă: {prevLesson.title}</span>
                </Link>
              ) : <div />}

              {nextLesson ? (
                <Link
                  href={`/courses/${course.id}/lesson/${nextLesson.id}`}
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#315D50] text-white hover:bg-[#23473C] text-xs font-semibold transition-colors shadow-xs"
                >
                  <span>Următoarea Lecție</span>
                  <ChevronRight className="w-4 h-4" />
                </Link>
              ) : (
                <Link
                  href={`/courses/${course.id}`}
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#3E6650] text-white hover:bg-[#045932] text-xs font-semibold transition-colors shadow-xs"
                >
                  <span>Finalizează Cursul & Obține Certificatul</span>
                  <Award className="w-4 h-4" />
                </Link>
              )}
            </div>

          </div>

          {/* Right Column (4 cols): Course Syllabus, Notes, Flashcards */}
          <div className="lg:col-span-4 space-y-4">
            
            {/* Sidebar Tab Selector */}
            <div className="bg-white border border-[#DFE3D9] rounded-lg p-1 flex items-center shadow-xs">
              <button
                onClick={() => setRightTab('syllabus')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  rightTab === 'syllabus' ? 'bg-[#EDF2E9] text-[#315D50]' : 'text-[#68736B] hover:text-[#25382F]'
                }`}
              >
                Programă
              </button>
              <button
                onClick={() => setRightTab('notes')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  rightTab === 'notes' ? 'bg-[#EDF2E9] text-[#315D50]' : 'text-[#68736B] hover:text-[#25382F]'
                }`}
              >
                Notițe
              </button>
              <button
                onClick={() => setRightTab('flashcards')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  rightTab === 'flashcards' ? 'bg-[#EDF2E9] text-[#315D50]' : 'text-[#68736B] hover:text-[#25382F]'
                }`}
              >
                Carduri 3D
              </button>
            </div>

            {/* Tab 1: Syllabus List */}
            {rightTab === 'syllabus' && (
              <div className="bg-white border border-[#DFE3D9] rounded-lg p-4 shadow-xs space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-[#ECEEE7]">
                  <h3 className="text-xs font-bold text-[#25382F] uppercase tracking-wide">
                    Modulele Cursului ({completedCount}/{allLessons.length})
                  </h3>
                  <span className="text-xs font-bold text-[#315D50]">
                    {courseProgressPercent}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full h-1.5 bg-[#DFE3D9] rounded-full overflow-hidden">
                  <div className="h-full bg-[#3E6650] rounded-full" style={{ width: `${courseProgressPercent}%` }} />
                </div>

                {/* Lessons List */}
                <div className="space-y-1.5 pt-2">
                  {allLessons.map((lsn) => {
                    const isCurrent = lsn.id === lesson.id;
                    return (
                      <Link
                        key={lsn.id}
                        href={`/courses/${course.id}/lesson/${lsn.id}`}
                        className={`flex items-center justify-between p-2.5 rounded-md text-xs transition-colors ${
                          isCurrent
                            ? 'bg-[#EDF2E9] text-[#315D50] font-bold border border-[#315D50]/30'
                            : 'hover:bg-[#F8F7F2] text-[#25382F] border border-transparent'
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                            lsn.completed
                              ? 'bg-[#3E6650] text-white'
                              : isCurrent
                              ? 'bg-[#315D50] text-white'
                              : 'bg-[#DFE3D9] text-[#68736B]'
                          }`}>
                            {lsn.completed ? '✓' : lsn.order_index}
                          </span>
                          <span className="truncate">{lsn.title}</span>
                        </div>
                        <span className="text-[11px] text-[#68736B] shrink-0 ml-2">
                          {lsn.duration || '2m'}
                        </span>
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Tab 2: Notes Editor */}
            {rightTab === 'notes' && (
              <div className="bg-white border border-[#DFE3D9] rounded-lg p-4 shadow-xs space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-[#ECEEE7]">
                  <h3 className="text-xs font-bold text-[#25382F] uppercase tracking-wide">
                    Caiet de Notițe Personale
                  </h3>
                  {noteSavedFeedback && (
                    <span className="text-xs text-[#3E6650] font-semibold flex items-center gap-1">
                      <Check className="w-3.5 h-3.5" /> Salvat!
                    </span>
                  )}
                </div>

                <textarea
                  rows={10}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Scrie notițe, idei cheie sau acțiuni concrete din această lecție..."
                  className="w-full p-3 text-xs bg-[#FAFAFA] border border-[#DFE3D9] rounded-md focus:border-[#315D50] outline-hidden text-[#25382F] resize-none leading-relaxed"
                />

                <div className="flex items-center justify-between pt-1">
                  <a
                    href={getLessonExportUrl(lesson.id, 'text')}
                    download
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-[#315D50] hover:underline"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Exportă Markdown (.md)</span>
                  </a>

                  <button
                    onClick={handleSaveNotes}
                    disabled={savingNotes}
                    className="px-4 py-1.5 rounded-full bg-[#315D50] hover:bg-[#23473C] text-white text-xs font-semibold transition-colors disabled:opacity-50 flex items-center gap-1 shadow-xs"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{savingNotes ? 'Se salvează...' : 'Salvează Notițe'}</span>
                  </button>
                </div>
              </div>
            )}

            {/* Tab 3: Flashcards Quick Widget */}
            {rightTab === 'flashcards' && (
              <div className="bg-white border border-[#DFE3D9] rounded-lg p-4 shadow-xs space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-[#ECEEE7]">
                  <h3 className="text-xs font-bold text-[#25382F] uppercase tracking-wide">
                    Card Memorare Activă ({fcIndex + 1}/{Math.max(1, lessonFlashcards.length)})
                  </h3>
                  <span className="text-[11px] text-[#68736B]">Apasă pentru răspuns</span>
                </div>

                <div
                  onClick={() => setFcFlipped(!fcFlipped)}
                  className="h-44 p-4 rounded-lg bg-[#FAFAFA] border border-[#DFE3D9] hover:border-[#315D50] flex flex-col justify-center items-center text-center cursor-pointer transition-all shadow-xs"
                >
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#315D50] mb-2">
                    {fcFlipped ? 'Răspuns Cheie' : 'Întrebare de Fixare'}
                  </span>
                  <p className="text-xs sm:text-sm font-semibold text-[#25382F] leading-relaxed">
                    {fcFlipped ? activeCard.answer : activeCard.question}
                  </p>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    onClick={() => {
                      setFcFlipped(false);
                      setFcIndex((prev) => Math.max(0, prev - 1));
                    }}
                    disabled={fcIndex === 0}
                    className="px-3 py-1 rounded-full text-xs font-semibold border border-[#DFE3D9] disabled:opacity-40 hover:bg-[#F8F7F2]"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => {
                      setFcFlipped(false);
                      setFcIndex((prev) => (prev + 1) % Math.max(1, lessonFlashcards.length));
                    }}
                    className="px-3 py-1 rounded-full text-xs font-semibold bg-[#315D50] text-white hover:bg-[#23473C]"
                  >
                    Următorul
                  </button>
                </div>
              </div>
            )}

          </div>

        </div>
      </div>
    </div>
  );
}

export default function ClassroomPage() {
  return (
    <Suspense fallback={
      <div className="max-w-[1200px] mx-auto px-4 py-8">
        <div className="h-[500px] bg-white rounded-lg border border-[#DFE3D9] animate-pulse" />
      </div>
    }>
      <ClassroomContent />
    </Suspense>
  );
}
