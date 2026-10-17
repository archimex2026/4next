'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  BookOpen, Play, CheckCircle2, Award, Clock, 
  Layers, Download, ChevronRight, Video, Headphones, 
  FileText, Sparkles, Check, Share2, Bookmark, Star, Users,
  CheckCircle, ArrowRight, ExternalLink, ShieldCheck, ChevronDown,
  BarChart2, Flame, Circle, CheckCircle as CheckIcon, AlertCircle
} from 'lucide-react';
import { fetchCourse, toggleLessonComplete, getLessonExportUrl } from '@/lib/api';
import { Course, Lesson } from '@/lib/types';

function CourseRoadmapContent() {
  const params = useParams();
  const router = useRouter();
  const courseId = params?.id as string;

  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [copied, setCopied] = useState(false);
  const [expandedLevels, setExpandedLevels] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!courseId) return;
    fetchCourse(courseId)
      .then((data) => {
        setCourse(data);
        if (data.levels) {
          const initial: Record<string, boolean> = {};
          data.levels.forEach((lvl) => { initial[lvl.id] = true; });
          setExpandedLevels(initial);
        }
      })
      .catch((err) => console.error('Course load error:', err))
      .finally(() => setLoading(false));
  }, [courseId]);

  const toggleLevel = (lvlId: string) => {
    setExpandedLevels((prev) => ({ ...prev, [lvlId]: !prev[lvlId] }));
  };

  const handleShare = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 py-8">
        <div className="h-96 bg-white rounded-xl border border-[#DFE3D9] animate-pulse" />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 py-16 text-center">
        <div className="w-12 h-12 rounded-full bg-[#EDF2E9] text-[#315D50] flex items-center justify-center mx-auto mb-3">
          <BookOpen className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-[#25382F]">Course Not Found</h2>
        <p className="text-xs text-[#68736B] mt-1">This course may have been removed or has not yet been synthesized.</p>
        <Link 
          href="/dashboard" 
          className="mt-4 inline-flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#315D50] text-white text-xs font-semibold hover:bg-[#23473C] transition-colors shadow-xs"
        >
          Return to My Learning
        </Link>
      </div>
    );
  }

  const allLessons = course.levels?.flatMap((lvl) => lvl.lessons) || [];
  const firstLessonId = allLessons[0]?.id || 'lsn-ls-1';
  const completedLessons = allLessons.filter((l) => l.completed).length;
  const progressPercent = allLessons.length > 0 ? Math.round((completedLessons / allLessons.length) * 100) : 33;
  const topicsCount = course.levels?.length || 3;
  const lessonsCount = allLessons.length || 6;
  const quizCount = course.quiz_count || 6;
  const flashcardsCount = course.flashcard_count || 12;

  // Determine difficulty per level or index
  const getDifficulty = (index: number) => {
    if (index < 2) return { label: 'Beginner', color: 'bg-emerald-50 text-[#3E6650] border-emerald-200' };
    if (index < 4) return { label: 'Intermediate', color: 'bg-blue-50 text-[#315D50] border-blue-200' };
    return { label: 'Advanced', color: 'bg-purple-50 text-purple-700 border-purple-200' };
  };

  // Dynamic skills list extracted from actual course curriculum and topics
  const dynamicSkills = course.levels?.flatMap((lvl) => {
    const cleanLvl = lvl.title.replace(/^Level \d+:\s*/i, '').replace(/^Topic \d+:\s*/i, '');
    const lsnSkills = lvl.lessons.map((l) => l.title.replace(/^(Mastering|Deconstructing|Mapping|Designing|Sprint \d+:)\s*/i, ''));
    return [cleanLvl, ...lsnSkills];
  }).filter((s) => s && s.length > 3).slice(0, 7) || [];

  const skillsList = dynamicSkills.length >= 4 ? dynamicSkills : [
    'System Architecture',
    'Domain Modeling',
    'Workflow Execution',
    'Validation Rules',
    'Core Frameworks',
    'Technical Deliverables'
  ];

  const authorName = course.book?.author || course.author || 'Author';
  const pageCount = course.book?.page_count || 120;

  return (
    <div className="min-h-screen bg-[#F8F7F2] pb-16">
      {/* ═══════════════════════════════════════════════════════
          BOOK DETAILS PAGE HERO BANNER
          ═══════════════════════════════════════════════════════ */}
      <section className="course-intro text-white py-10 px-4">
        <div className="max-w-[1280px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          {/* Left Metadata & Title */}
          <div className="lg:col-span-8 space-y-4">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-xs text-sky-200">
              <Link href="/" className="hover:underline">Acasă</Link>
              <span>/</span>
              <Link href="/dashboard" className="hover:underline">Cursurile Mele</Link>
              <span>/</span>
              <span className="text-white font-semibold truncate max-w-[280px] sm:max-w-none">{course.title}</span>
            </div>

            {/* Course Metadata Badges */}
            <div className="flex flex-wrap items-center gap-2 text-xs text-sky-200">
              <span className="px-2.5 py-0.5 rounded-full bg-[#E8EFE4] text-[#3E6650] font-bold text-[10px] tracking-wider uppercase">
                SPAȚIUL TĂU DE STUDIU
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                <span>{course.estimated_duration || '18 min'}</span>
              </span>
              <span>•</span>

            </div>

            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
              {course.title}
            </h1>

            <p className="text-sm text-slate-200 max-w-2xl leading-relaxed">
              {course.subtitle || course.overview}
            </p>

            {/* Author Line */}
            <div className="flex items-center gap-2.5 pt-1 text-xs text-slate-200">
              <div className="w-6 h-6 rounded-full bg-[#315D50] border border-white/40 text-white font-bold text-[10px] flex items-center justify-center">
                {authorName.charAt(0)}
              </div>
              <span>
                De <strong className="text-white">{authorName}</strong>
              </span>
              <span>•</span>
              <span>Sintetizat din manuscrisul de {pageCount} pagini</span>
            </div>

            {/* CTA Action Buttons */}
            <div className="pt-3 flex flex-wrap items-center gap-3">
              <Link
                href={`/courses/${course.id}/lesson/${firstLessonId}`}
                className="px-6 py-2.5 rounded-full bg-white text-[#315D50] hover:bg-slate-100 text-sm font-bold transition-all flex items-center gap-2 shadow-md active:scale-98"
              >
                <Headphones className="w-4 h-4 text-[#315D50]" />
                <span>Începe să înveți</span>
              </Link>

              <Link
                href={`/courses/${course.id}/video/${firstLessonId}`}
                className="px-5 py-2.5 rounded-full bg-white/10 hover:bg-white/20 text-white border border-white/25 text-sm font-semibold transition-colors flex items-center gap-2"
              >
                <Video className="w-4 h-4" />
                <span>Explorează video</span>
              </Link>

              <button
                onClick={() => setSaved(!saved)}
                className={`px-4 py-2.5 rounded-full border text-sm font-semibold transition-colors flex items-center gap-1.5 ${
                  saved
                    ? 'bg-white text-[#315D50] border-white'
                    : 'border-white/30 text-white hover:bg-white/10'
                }`}
              >
                <Bookmark className={`w-4 h-4 ${saved ? 'fill-current' : ''}`} />
                <span>{saved ? 'Salvat' : 'Salvează'}</span>
              </button>

              <button
                onClick={handleShare}
                className="px-4 py-2.5 rounded-full border border-white/30 text-white hover:bg-white/10 text-sm font-semibold transition-colors flex items-center gap-1.5"
              >
                <Share2 className="w-4 h-4" />
                <span>{copied ? 'Link Copiat!' : 'Distribuie'}</span>
              </button>
            </div>
          </div>


          {/* Right: BOOK COVER DISPLAY */}
          <div className="lg:col-span-4">
            <div className="bg-white rounded-xl overflow-hidden border border-[#DFE3D9] shadow-xl text-[#25382F]">
              {/* 3D Book Cover Visual */}
              <div className="p-5 bg-gradient-to-br from-[#F8FAFC] to-[#EDF3F8] border-b border-[#DFE3D9] flex justify-center">
                <div className="relative w-44 h-60 rounded-md bg-gradient-to-br from-[#223D33] via-[#315D50] to-[#5D8271] text-white p-4 flex flex-col justify-between shadow-[8px_12px_24px_rgba(0,0,0,0.2)] border-l-4 border-l-[#001D33] transform hover:-rotate-1 transition-transform">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded bg-white/20 text-sky-100">
                      MATERIAL DE STUDIU
                    </span>
                    <span className="text-[10px] font-mono text-sky-200">
                      {pageCount} p.
                    </span>
                  </div>

                  <div className="my-auto space-y-1">
                    <h3 className="text-sm font-bold leading-snug text-white">
                      {course.book?.title || course.title}
                    </h3>
                    <p className="text-[11px] text-sky-200 font-medium">
                      {authorName}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-white/20 flex items-center justify-between text-[9px] text-sky-200 uppercase font-bold tracking-wider">
                    <span>4next</span>
                    <span>În ritmul tău</span>
                  </div>
                </div>
              </div>

              {/* Quick Launch Actions */}
              <div className="p-4 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#25382F]">Alege cum înveți</span>
                  <span className="text-[11px] text-[#3E6650] font-semibold flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    De explorat
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <Link
                    href={`/courses/${course.id}/video/${firstLessonId}`}
                    className="flex items-center justify-between p-2 rounded-lg bg-[#F8FAFC] hover:bg-[#EDF2E9] transition-colors"
                  >
                    <span className="flex items-center gap-2 font-semibold text-[#25382F]">
                      <Video className="w-4 h-4 text-[#3E6650]" />
                      <span>{lessonsCount} lecții video</span>
                    </span>
                    <span className="text-[11px] text-[#315D50] font-bold">Vezi &rarr;</span>
                  </Link>

                  <Link
                    href={`/courses/${course.id}/lesson/${firstLessonId}`}
                    className="flex items-center justify-between p-2 rounded-lg bg-[#F8FAFC] hover:bg-[#EDF2E9] transition-colors"
                  >
                    <span className="flex items-center gap-2 font-semibold text-[#25382F]">
                      <Headphones className="w-4 h-4 text-[#5D8271]" />
                      <span>Lecții și explicații audio</span>
                    </span>
                    <span className="text-[11px] text-[#315D50] font-bold">Deschide &rarr;</span>
                  </Link>

                  <Link
                    href={`/courses/${course.id}/flashcards`}
                    className="flex items-center justify-between p-2 rounded-lg bg-[#F8FAFC] hover:bg-[#EDF2E9] transition-colors"
                  >
                    <span className="flex items-center gap-2 font-semibold text-[#25382F]">
                      <Layers className="w-4 h-4 text-[#D97706]" />
                      <span>{flashcardsCount} Flashcards</span>
                    </span>
                    <span className="text-[11px] text-[#315D50] font-bold">Exersează &rarr;</span>
                  </Link>
                </div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════
          BOOK DETAILS METRICS BAR (Exact Spec Display)
          - Book Cover
          - Progress Bar
          - Module
          - Lecții
          - Întrebări
          - Flashcarduri
          - Lecții video
          - Lecții audio
          ═══════════════════════════════════════════════════════ */}
      <div className="max-w-[1280px] mx-auto px-4 -mt-4 z-20 relative">
        <div className="bg-white rounded-xl border border-[#DFE3D9] p-5 shadow-sm space-y-4">
          
          {/* Progress Bar Section */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-[#25382F] flex items-center gap-2">
                <span>Progresul tău</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#EDF2E9] text-[#315D50]">
                  {completedLessons} din {lessonsCount} lecții
                </span>
              </span>
              <span className="font-bold text-[#315D50] text-sm">{progressPercent}%</span>
            </div>
            <div className="w-full bg-[#DFE3D9] h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-[#315D50] h-full rounded-full transition-all duration-500 shadow-2xs"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* 6-Metric Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2 border-t border-[#ECEEE7]">
            {/* 1. Module */}
            <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#DFE3D9] text-center">
              <p className="text-xl font-extrabold text-[#315D50]">{topicsCount}</p>
              <p className="text-[10px] uppercase font-bold text-[#68736B] mt-0.5">Module</p>
            </div>

            {/* 2. Lecții */}
            <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#DFE3D9] text-center">
              <p className="text-xl font-extrabold text-[#3E6650]">{lessonsCount}</p>
              <p className="text-[10px] uppercase font-bold text-[#68736B] mt-0.5">Lecții</p>
            </div>

            {/* 3. Întrebări */}
            <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#DFE3D9] text-center">
              <p className="text-xl font-extrabold text-[#8B5CF6]">{quizCount}</p>
              <p className="text-[10px] uppercase font-bold text-[#68736B] mt-0.5">Întrebări</p>
            </div>

            {/* 4. Flashcarduri */}
            <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#DFE3D9] text-center">
              <p className="text-xl font-extrabold text-[#D97706]">{flashcardsCount}</p>
              <p className="text-[10px] uppercase font-bold text-[#68736B] mt-0.5">Flashcarduri</p>
            </div>

            {/* 5. Lecții video */}
            <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#DFE3D9] text-center">
              <p className="text-xl font-extrabold text-[#3E6650]">{lessonsCount} HD</p>
              <p className="text-[10px] uppercase font-bold text-[#68736B] mt-0.5">Lecții video</p>
            </div>

            {/* 6. Lecții audio */}
            <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#DFE3D9] text-center">
              <p className="text-xl font-extrabold text-[#5D8271]">{lessonsCount} MP3</p>
              <p className="text-[10px] uppercase font-bold text-[#68736B] mt-0.5">Audio (RO / EN)</p>
            </div>
          </div>

          {/* Quick Export / Save Toolbar for Course */}
          <div className="pt-3 border-t border-[#ECEEE7] flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Download className="w-4 h-4 text-[#315D50]" />
              <span className="text-xs font-bold text-[#25382F]">Salvează Resursele Generate:</span>
              <span className="text-[11px] text-[#68736B]">1-clic descărcare directă din studio</span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <a
                href={getLessonExportUrl(firstLessonId, 'audio', 'ro')}
                download
                className="px-3 py-1 rounded-full bg-[#EDF2E9] hover:bg-[#315D50] text-[#315D50] hover:text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-2xs"
                title="Descarcă Audio MP3"
              >
                <Headphones className="w-3.5 h-3.5" />
                <span>Audio MP3 (RO)</span>
              </a>

              <a
                href={getLessonExportUrl(firstLessonId, 'video')}
                download
                className="px-3 py-1 rounded-full bg-[#E8EFE4] hover:bg-[#3E6650] text-[#3E6650] hover:text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-2xs"
                title="Descarcă Video MP4"
              >
                <Video className="w-3.5 h-3.5" />
                <span>Video MP4</span>
              </a>

              <a
                href={getLessonExportUrl(firstLessonId, 'diagram')}
                download
                className="px-3 py-1 rounded-full bg-[#F3E8FF] hover:bg-[#8B5CF6] text-[#8B5CF6] hover:text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-2xs"
                title="Descarcă Diagrame Mermaid .mmd"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Diagrame .MMD</span>
              </a>

              <a
                href={getLessonExportUrl(firstLessonId, 'text')}
                download
                className="px-3 py-1 rounded-full bg-[#FFFBEB] hover:bg-[#D97706] text-[#D97706] hover:text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-2xs"
                title="Descarcă Sinteză Text & Notițe .md"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Text / Markdown</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════
          PARCURS DE STUDIU
          ═══════════════════════════════════════════════════════ */}
      <div className="max-w-[1280px] mx-auto px-4 pt-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Main Roadmap Tree Column */}
          <div className="lg:col-span-8 space-y-6">
            <div className="bg-white rounded-xl border border-[#DFE3D9] p-6 shadow-xs space-y-6">
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-[#ECEEE7]">
                <div>
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-[#315D50] text-white flex items-center justify-center font-bold text-xs shadow-2xs">
                      <BookOpen className="w-4 h-4" />
                    </div>
                    <h2 className="text-lg font-bold text-[#25382F]">
                      Curriculum Structurat pe Capitole
                    </h2>
                  </div>
                  <p className="text-xs text-[#68736B] mt-1">
                    Parcurge ideile pas cu pas, de la conceptele de bază la aplicare.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Link
                    href={`/courses/${course.id}/video/${firstLessonId}`}
                    className="px-4 py-1.5 rounded-full bg-[#315D50] hover:bg-[#23473C] text-white text-xs font-semibold transition-colors flex items-center gap-1.5"
                  >
                    <Play className="w-3.5 h-3.5 fill-white" />
                    <span>Deschide Video Tutorial</span>
                  </Link>
                </div>
              </div>

              {/* TREE ROADMAP VISUAL DISPLAY */}
              <div className="relative pl-6 sm:pl-8 space-y-8 before:absolute before:left-3 sm:before:left-4 before:top-3 before:bottom-3 before:w-0.5 before:bg-[#315D50]/30">
                
                {/* Course Root Node */}
                <div className="relative">
                  <div className="absolute -left-6 sm:-left-8 top-1 w-6 h-6 rounded-full bg-[#315D50] text-white flex items-center justify-center text-xs font-bold shadow-xs">
                    ✦
                  </div>
                  <div className="bg-[#F8FAFC] border border-[#DFE3D9] rounded-lg p-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#315D50]">Root Curriculum</span>
                    <h3 className="text-sm font-bold text-[#25382F]">{course.title}</h3>
                  </div>
                </div>

                {/* Levels & Lessons Breakdown */}
                {course.levels?.map((lvl, lvlIdx) => (
                  <div key={lvl.id} className="space-y-4">
                    {/* Level / Section Header */}
                    <div className="relative">
                      <div className="absolute -left-6 sm:-left-8 top-1.5 w-6 h-6 rounded-full bg-white border-2 border-[#315D50] text-[#315D50] flex items-center justify-center text-xs font-bold shadow-2xs">
                        {lvl.level_number}
                      </div>
                      <div className="flex items-center justify-between pb-1">
                        <div>
                          <span className="text-[11px] font-bold text-[#315D50] uppercase tracking-wider">
                            Topic {lvl.level_number}
                          </span>
                          <h4 className="text-sm font-bold text-[#25382F]">{lvl.title}</h4>
                        </div>
                        <span className="text-xs text-[#68736B]">{lvl.lessons.length} lessons</span>
                      </div>
                    </div>

                    {/* Lessons under this topic */}
                    <div className="space-y-3 pl-2 sm:pl-4">
                      {lvl.lessons.map((lsn, lsnIdx) => {
                        const globalIndex = lvlIdx * 2 + lsnIdx;
                        const difficulty = getDifficulty(globalIndex);
                        const isDone = lsn.completed;
                        const lessonProgress = isDone ? 100 : (globalIndex === 0 ? 50 : 0);

                        return (
                          <div 
                            key={lsn.id}
                            className="bg-white border border-[#DFE3D9] hover:border-[#315D50] rounded-xl p-4 shadow-2xs hover:shadow-xs transition-all space-y-3 group"
                          >
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                              {/* Left Lesson Info */}
                              <div className="flex items-start gap-3">
                                {/* Completion Status Indicator */}
                                <div className="mt-0.5 shrink-0">
                                  {isDone ? (
                                    <div className="w-5 h-5 rounded-full bg-[#E8EFE4] text-[#3E6650] flex items-center justify-center" title="Lesson Completed">
                                      <CheckCircle2 className="w-5 h-5" />
                                    </div>
                                  ) : lessonProgress > 0 ? (
                                    <div className="w-5 h-5 rounded-full bg-[#EDF2E9] text-[#315D50] flex items-center justify-center font-bold text-[10px]" title="In Progress">
                                      ◷
                                    </div>
                                  ) : (
                                    <div className="w-5 h-5 rounded-full border-2 border-[#C4C9D0] text-transparent group-hover:border-[#315D50] flex items-center justify-center" title="Not Started">
                                      <Circle className="w-3 h-3" />
                                    </div>
                                  )}
                                </div>

                                <div>
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className="text-[11px] font-bold text-[#68736B]">
                                      Lesson {lsn.order_index}
                                    </span>
                                    {/* Difficulty Badge */}
                                    <span className={`px-2 py-0.2 rounded text-[10px] font-bold border ${difficulty.color}`}>
                                      {difficulty.label}
                                    </span>
                                    {/* Duration */}
                                    <span className="flex items-center gap-1 text-[11px] text-[#68736B] font-mono">
                                      <Clock className="w-3 h-3" />
                                      {lsn.duration || '3m 30s'}
                                    </span>
                                  </div>

                                  <Link
                                    href={`/courses/${course.id}/lesson/${lsn.id}`}
                                    className="text-sm font-bold text-[#25382F] group-hover:text-[#315D50] transition-colors mt-0.5 block"
                                  >
                                    {lsn.title}
                                  </Link>
                                </div>
                              </div>

                              {/* Right Quick Actions */}
                              <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                                <Link
                                  href={`/courses/${course.id}/video/${lsn.id}`}
                                  className="px-3 py-1 rounded-full bg-[#EDF2E9] hover:bg-[#315D50] text-[#315D50] hover:text-white text-xs font-semibold transition-colors flex items-center gap-1"
                                  title="Watch Video Lesson"
                                >
                                  <Video className="w-3.5 h-3.5" />
                                  <span>Video</span>
                                </Link>

                                <Link
                                  href={`/courses/${course.id}/lesson/${lsn.id}`}
                                  className="px-3 py-1 rounded-full border border-[#DFE3D9] hover:border-[#315D50] hover:bg-white text-xs font-semibold text-[#25382F] transition-colors"
                                >
                                  Read
                                </Link>
                              </div>
                            </div>

                            {/* Lesson Progress Sub-bar */}
                            <div className="space-y-1 pt-1">
                              <div className="flex items-center justify-between text-[11px] text-[#68736B]">
                                <span>Completion status: <strong className="text-[#25382F]">{isDone ? 'Completed' : (lessonProgress > 0 ? 'In Progress' : 'Not Started')}</strong></span>
                                <span className="font-semibold text-[#315D50]">{lessonProgress}%</span>
                              </div>
                              <div className="w-full bg-[#DFE3D9] h-1.5 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all duration-300 ${
                                    isDone ? 'bg-[#3E6650]' : 'bg-[#315D50]'
                                  }`}
                                  style={{ width: `${lessonProgress}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}

                {/* Road Map Milestone: Quiz */}
                <div className="relative">
                  <div className="absolute -left-6 sm:-left-8 top-1.5 w-6 h-6 rounded-full bg-[#8B5CF6] text-white flex items-center justify-center text-xs font-bold shadow-xs">
                    ★
                  </div>
                  <div className="bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#8B5CF6]">
                        Milestone Assessment
                      </span>
                      <h4 className="text-sm font-bold text-[#25382F]">
                        ├ Chapter Quiz: {course.title}
                      </h4>
                      <p className="text-xs text-[#68736B]">
                        6 multiple-choice questions with detailed answer rationale • 70% required to pass
                      </p>
                    </div>

                    <Link
                      href={`/courses/${course.id}/quiz`}
                      className="px-4 py-2 rounded-full bg-[#8B5CF6] hover:bg-[#7C3AED] text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shrink-0 self-start sm:self-center shadow-2xs"
                    >
                      <Award className="w-3.5 h-3.5" />
                      <span>Take Quiz</span>
                    </Link>
                  </div>
                </div>

                {/* Road Map Milestone: Flashcards */}
                <div className="relative">
                  <div className="absolute -left-6 sm:-left-8 top-1.5 w-6 h-6 rounded-full bg-[#D97706] text-white flex items-center justify-center text-xs font-bold shadow-xs">
                    🗂
                  </div>
                  <div className="bg-[#FFFBEB] border border-[#FDE68A] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#D97706]">
                        Active Recall Deck
                      </span>
                      <h4 className="text-sm font-bold text-[#25382F]">
                        ├ Flashcards: Key Mental Models & Principles
                      </h4>
                      <p className="text-xs text-[#68736B]">
                        12 3D flippable cards with keyboard controls (Space to flip, arrows to navigate)
                      </p>
                    </div>

                    <Link
                      href={`/courses/${course.id}/flashcards`}
                      className="px-4 py-2 rounded-full bg-[#D97706] hover:bg-[#B45309] text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shrink-0 self-start sm:self-center shadow-2xs"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Practice Cards</span>
                    </Link>
                  </div>
                </div>

              </div>
            </div>

            {/* Author Profile */}
            <div className="bg-white rounded-xl border border-[#DFE3D9] p-6 shadow-xs flex flex-col sm:flex-row items-start gap-4">
              <div className="w-14 h-14 rounded-full bg-[#315D50] text-white font-bold text-xl flex items-center justify-center shrink-0">
                {authorName.charAt(0)}
              </div>
              <div className="flex-1 space-y-1">
                <h3 className="text-base font-bold text-[#25382F]">{authorName}</h3>
                <p className="text-xs text-[#68736B]">Author & Domain Specialist • Educational Synthesis</p>
                <p className="text-xs text-[#25382F] pt-2 leading-relaxed">
                  Extracted and synthesized into actionable micro-learning lessons, Mermaid architecture diagrams, and studio media by 4next.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Interactive Study Tools & Skills */}
          <aside className="lg:col-span-4 space-y-6">
            
            {/* Quick Practice Hub */}
            <div className="bg-white rounded-xl border border-[#DFE3D9] p-5 shadow-xs space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#25382F]">
                Interactive Study Tools
              </h3>

              <Link
                href={`/courses/${course.id}/video/${firstLessonId}`}
                className="flex items-center justify-between p-3 rounded-lg border border-[#DFE3D9] hover:bg-[#F8FAFC] hover:border-[#315D50] transition-colors text-xs font-semibold text-[#25382F] group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#E8EFE4] text-[#3E6650] flex items-center justify-center shrink-0">
                    <Video className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="block group-hover:text-[#315D50]">Cinema Video Player</span>
                    <span className="text-[11px] text-[#68736B] font-normal">{lessonsCount} 720p HD Lessons</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-[#7C857B] group-hover:text-[#315D50]" />
              </Link>

              <Link
                href={`/courses/${course.id}/flashcards`}
                className="flex items-center justify-between p-3 rounded-lg border border-[#DFE3D9] hover:bg-[#F8FAFC] hover:border-[#315D50] transition-colors text-xs font-semibold text-[#25382F] group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#FEF3C7] text-[#D97706] flex items-center justify-center shrink-0">
                    <Layers className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="block group-hover:text-[#315D50]">3D Active Recall Deck</span>
                    <span className="text-[11px] text-[#68736B] font-normal">{flashcardsCount} Mental Models</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-[#7C857B] group-hover:text-[#315D50]" />
              </Link>

              <Link
                href={`/courses/${course.id}/quiz`}
                className="flex items-center justify-between p-3 rounded-lg border border-[#DFE3D9] hover:bg-[#F8FAFC] hover:border-[#315D50] transition-colors text-xs font-semibold text-[#25382F] group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#F3E8FF] text-[#8B5CF6] flex items-center justify-center shrink-0">
                    <Award className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="block group-hover:text-[#315D50]">Test de Verificare Cunoștințe</span>
                    <span className="text-[11px] text-[#68736B] font-normal">Obține Certificat de Absolvire</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-[#7C857B] group-hover:text-[#315D50]" />
              </Link>
            </div>

            {/* Skills Covered Pill Box */}
            <div className="bg-white rounded-xl border border-[#DFE3D9] p-5 shadow-xs space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#25382F]">
                Concepte & Competențe
              </h3>
              <div className="flex flex-wrap gap-2">
                {skillsList.map((skill) => (
                  <span 
                    key={skill} 
                    className="px-2.5 py-1 rounded-full text-xs font-medium bg-[#F8F7F2] text-[#25382F] border border-[#DFE3D9] hover:border-[#315D50] transition-colors"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Certificate Box */}
            <div className="bg-white rounded-xl border border-[#DFE3D9] p-5 shadow-xs space-y-3">
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-amber-500" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#25382F]">
                  Certificat de Absolvire
                </h3>
              </div>
              <p className="text-xs text-[#68736B] leading-relaxed">
                Parcurge cele {lessonsCount} lecții, apoi verifică ce ai reținut cu întrebările de recapitulare.
              </p>
              <Link
                href={`/courses/${course.id}/quiz`}
                className="block text-center py-2 px-3 rounded-full bg-[#315D50] hover:bg-[#23473C] text-white text-xs font-semibold transition-colors shadow-2xs"
              >
                Susține Testul Final
              </Link>
            </div>

          </aside>
        </div>
      </div>
    </div>
  );
}

export default function CourseRoadmapPage() {
  return (
    <Suspense fallback={<div className="max-w-[1280px] mx-auto px-4 py-8"><div className="h-96 bg-white rounded-xl animate-pulse" /></div>}>
      <CourseRoadmapContent />
    </Suspense>
  );
}
