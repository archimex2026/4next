'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  Play, Pause, SkipBack, SkipForward, Volume2, VolumeX,
  Maximize2, CheckCircle2, ArrowLeft, ArrowRight,
  BookOpen, Clock, Layers, Award, Sparkles, Save, Check, FileText,
  RotateCcw, RotateCw, Video, Headphones, Download, GitGraph,
  ExternalLink, ChevronRight, Mic, RefreshCw
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { fetchLesson, fetchCourse, toggleLessonComplete, saveLessonNotes, fetchQuizzes, getMediaUrl, getLessonExportUrl, generateLessonAudio } from '@/lib/api';
import { Lesson, Course, QuizQuestion } from '@/lib/types';
import MermaidDiagram from '@/components/MermaidDiagram';

function VideoPlayerContent() {
  const params = useParams();
  const router = useRouter();
  const courseId = params?.id as string;
  const lessonId = params?.lessonId as string;

  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [quizzes, setQuizzes] = useState<QuizQuestion[]>([]);
  const [selectedLang, setSelectedLang] = useState<'ro' | 'en'>('ro');

  // Video & Audio playback state
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(180);
  const [videoError, setVideoError] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [completed, setCompleted] = useState(false);

  // Neural Voice Selection & Regeneration
  const [selectedVoice, setSelectedVoice] = useState<'ro-RO-AlinaNeural' | 'ro-RO-EmilNeural'>('ro-RO-AlinaNeural');
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  // Active Tab below video: 'diagram' | 'transcript' | 'notes' | 'quiz'
  const [activeTab, setActiveTab] = useState<'diagram' | 'transcript' | 'notes' | 'quiz'>('diagram');

  // Notes state
  const [notes, setNotes] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  const [noteSavedFeedback, setNoteSavedFeedback] = useState(false);

  // Quiz state
  const [quizAnswers, setQuizAnswers] = useState<Record<string, number>>({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);

  useEffect(() => {
    if (!lessonId || !courseId) return;
    setLoading(true);

    Promise.all([
      fetchLesson(lessonId, selectedLang),
      fetchCourse(courseId),
      fetchQuizzes(courseId)
    ])
      .then(([lessonData, courseData, quizData]) => {
        setLesson(lessonData);
        setCourse(courseData);
        setQuizzes(quizData);
        setCompleted(lessonData.completed);
        setNotes(lessonData.notes || '');
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [lessonId, courseId]);

  const handleTimeUpdate = () => {
    const el = (!videoError && videoRef.current) ? videoRef.current : audioRef.current;
    if (el) {
      setCurrentTime(el.currentTime);
      if (el.duration && !isNaN(el.duration)) {
        setDuration(el.duration);
      }
      if (!completed && el.duration > 0 && (el.currentTime / el.duration) > 0.9) {
        handleMarkComplete();
      }
    }
  };

  const togglePlay = () => {
    const el = (!videoError && videoRef.current) ? videoRef.current : audioRef.current;
    if (!el) return;
    if (isPlaying) {
      el.pause();
      setIsPlaying(false);
    } else {
      el.play().then(() => setIsPlaying(true)).catch((e) => console.log('Media play:', e));
    }
  };

  const handleSeek = (timeSec: number) => {
    const el = (!videoError && videoRef.current) ? videoRef.current : audioRef.current;
    if (el) {
      el.currentTime = timeSec;
      setCurrentTime(timeSec);
    }
  };

  const handleSkip = (seconds: number) => {
    const el = (!videoError && videoRef.current) ? videoRef.current : audioRef.current;
    if (el) {
      const next = Math.max(0, Math.min(duration, el.currentTime + seconds));
      el.currentTime = next;
      setCurrentTime(next);
    }
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackRate(speed);
    if (videoRef.current) videoRef.current.playbackRate = speed;
    if (audioRef.current) audioRef.current.playbackRate = speed;
  };

  const handleVolumeChange = (newVol: number) => {
    setVolume(newVol);
    setIsMuted(newVol === 0);
    if (videoRef.current) videoRef.current.volume = newVol;
    if (audioRef.current) audioRef.current.volume = newVol;
  };

  const handleMarkComplete = async () => {
    if (!lesson || completed) return;
    try {
      await toggleLessonComplete(lesson.id);
      setCompleted(true);
      confetti({ particleCount: 70, spread: 60, origin: { y: 0.7 } });
    } catch (e) {
      console.error(e);
    }
  };

  const handleRegenerateAudio = async () => {
    if (!lesson || isRegenerating) return;
    setIsRegenerating(true);
    setNotice('Generare voce neurală românească de înaltă definiție...');
    try {
      const updated = await generateLessonAudio(lesson.id, selectedVoice, selectedLang, '+0%');
      setLesson(updated);
      setNotice('Voce neurală generată cu succes!');
      setTimeout(() => setNotice(null), 3000);
      if (audioRef.current) {
        audioRef.current.src = getMediaUrl(selectedLang === 'ro' ? updated.audio_url_ro : updated.audio_url_en);
        audioRef.current.load();
        audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
      }
    } catch (e) {
      console.error(e);
      setNotice('Eroare la generare. Reîncercați.');
      setTimeout(() => setNotice(null), 3000);
    } finally {
      setIsRegenerating(false);
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

  const formatTime = (secs: number) => {
    if (isNaN(secs) || secs < 0) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
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

  const activeAudioUrl = selectedLang === 'ro'
    ? (lesson.audio_url_ro || lesson.active_audio_url || lesson.audio_url)
    : (lesson.audio_url_en || lesson.active_audio_url || lesson.audio_url);

  const activeVideoUrl = lesson.video_url;
  const activeTranscript = (selectedLang === 'ro' ? lesson.transcript_ro : lesson.transcript_en) || lesson.transcript || [];
  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="min-h-screen bg-[#F8F7F2] text-[#25382F] pb-16">
      
      {/* Subheader Bar - LinkedIn Enterprise Style */}
      <div className="bg-white border-b border-[#DFE3D9] px-4 py-3 sticky top-[56px] z-40 shadow-xs">
        <div className="max-w-[1200px] mx-auto flex flex-wrap items-center justify-between gap-3">
          
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
                  Lecția Video {lesson.order_index} din {allLessons.length}
                </span>
              </div>
              <h1 className="text-sm sm:text-base font-bold text-[#25382F] truncate">
                {lesson.title}
              </h1>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {/* Language Switcher */}
            <div className="flex items-center border border-[#DFE3D9] rounded-full p-0.5 bg-[#F8F7F2] text-xs font-semibold">
              <button
                type="button"
                onClick={() => {
                  setSelectedLang('ro');
                  fetchLesson(lesson.id, 'ro').then((u) => setLesson(u));
                }}
                className={`px-2.5 py-1 rounded-full transition-all ${
                  selectedLang === 'ro' ? 'bg-white text-[#315D50] shadow-xs' : 'text-[#68736B]'
                }`}
              >
                🇷🇴 Română
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedLang('en');
                  fetchLesson(lesson.id, 'en').then((u) => setLesson(u));
                }}
                className={`px-2.5 py-1 rounded-full transition-all ${
                  selectedLang === 'en' ? 'bg-white text-[#315D50] shadow-xs' : 'text-[#68736B]'
                }`}
              >
                🇬🇧 English
              </button>
            </div>

            <Link
              href={`/courses/${course.id}/lesson/${lesson.id}`}
              className="px-3.5 py-1.5 rounded-full border border-[#DFE3D9] hover:border-[#315D50] bg-white text-[#25382F] text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <FileText className="w-3.5 h-3.5 text-[#315D50]" />
              <span className="hidden sm:inline">Mod Text & Notițe</span>
            </Link>

            <button
              onClick={handleMarkComplete}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-xs ${
                completed ? 'bg-[#3E6650] text-white' : 'bg-[#315D50] hover:bg-[#23473C] text-white'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{completed ? 'Finalizat ✓' : 'Marchează Finalizat'}</span>
            </button>
          </div>

        </div>
      </div>

      {/* Main Classroom Content */}
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Main Media Stage (8 cols) */}
          <div className="lg:col-span-8 space-y-4">
            
            {/* Video / Interactive Stage Box */}
            <div className="bg-white border border-[#DFE3D9] rounded-lg overflow-hidden shadow-xs">
              
              <div className="relative aspect-video bg-[#25382F] flex items-center justify-center overflow-hidden">
                {!videoError && activeVideoUrl ? (
                  <video
                    ref={videoRef}
                    src={getMediaUrl(activeVideoUrl)}
                    onTimeUpdate={handleTimeUpdate}
                    onEnded={() => { setIsPlaying(false); handleMarkComplete(); }}
                    onError={() => setVideoError(true)}
                    className="w-full h-full object-contain"
                  />
                ) : (
                  /* Audio fallback visualizer */
                  <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center bg-gradient-to-br from-[#315D50] to-[#223D33] text-white">
                    <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center mb-3">
                      <Headphones className="w-8 h-8 text-white" />
                    </div>
                    <span className="text-xs uppercase tracking-widest font-bold text-[#EDF2E9] mb-1">
                      Narațiune Audio Didactică
                    </span>
                    <h3 className="text-lg font-bold text-white max-w-md">
                      {lesson.title}
                    </h3>
                    <p className="text-xs text-white/80 max-w-sm mt-1">
                      Explicații audio în română
                    </p>
                  </div>
                )}

                {/* Hidden Audio element if video is missing or for audio backup */}
                <audio
                  ref={audioRef}
                  src={getMediaUrl(activeAudioUrl)}
                  onTimeUpdate={handleTimeUpdate}
                  onEnded={() => { setIsPlaying(false); handleMarkComplete(); }}
                />
              </div>

              {/* Progress Scrub Bar */}
              <div 
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const clickPos = (e.clientX - rect.left) / rect.width;
                  handleSeek(clickPos * duration);
                }}
                className="w-full h-2 bg-[#DFE3D9] hover:h-2.5 rounded-none cursor-pointer transition-all relative overflow-hidden"
              >
                <div 
                  className="absolute left-0 top-0 bottom-0 bg-[#315D50] transition-all duration-75"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>

              {/* Controls Bar - Clean LinkedIn White Style */}
              <div className="p-4 bg-white flex flex-wrap items-center justify-between gap-3 border-t border-[#ECEEE7]">
                
                {/* Play / Skip Buttons */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleSkip(-10)}
                    className="p-1.5 rounded-full hover:bg-[#F8F7F2] text-[#68736B] hover:text-[#25382F]"
                    title="Înapoi 10 secunde"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>

                  <button
                    onClick={togglePlay}
                    className="w-10 h-10 rounded-full bg-[#315D50] hover:bg-[#23473C] text-white flex items-center justify-center shadow-xs transition-colors"
                  >
                    {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
                  </button>

                  <button
                    onClick={() => handleSkip(10)}
                    className="p-1.5 rounded-full hover:bg-[#F8F7F2] text-[#68736B] hover:text-[#25382F]"
                    title="Înainte 10 secunde"
                  >
                    <RotateCw className="w-4 h-4" />
                  </button>

                  <span className="text-xs font-medium text-[#68736B] ml-2">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>

                {/* Speed Controls */}
                <div className="flex items-center gap-1 border border-[#DFE3D9] rounded-full p-0.5 bg-[#F8F7F2]">
                  {[1, 1.25, 1.5, 2].map((spd) => (
                    <button
                      key={spd}
                      onClick={() => handleSpeedChange(spd)}
                      className={`px-2 py-0.5 text-[11px] font-semibold rounded-full transition-all ${
                        playbackRate === spd ? 'bg-white text-[#315D50] shadow-xs' : 'text-[#68736B]'
                      }`}
                    >
                      {spd}x
                    </button>
                  ))}
                </div>

                {/* Volume & Downloads */}
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5">
                    <Volume2 className="w-4 h-4 text-[#68736B]" />
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={volume}
                      onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                      className="w-16 h-1 bg-[#DFE3D9] accent-[#315D50] rounded-lg cursor-pointer"
                    />
                  </div>

                  {activeAudioUrl && (
                    <a
                      href={getMediaUrl(activeAudioUrl)}
                      download
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 rounded-full text-[#68736B] hover:text-[#25382F] hover:bg-[#F8F7F2]"
                      title="Descarcă MP3"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  )}
                </div>

              </div>

            </div>

            {/* Neural Voice Control Banner */}
            <div className="bg-white border border-[#DFE3D9] rounded-lg p-3 shadow-xs flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Mic className="w-4 h-4 text-[#315D50]" />
                <span className="text-xs font-bold text-[#25382F]">Alege vocea:</span>
                <div className="flex items-center border border-[#DFE3D9] rounded-full p-0.5 bg-[#F8F7F2]">
                  <button
                    onClick={() => setSelectedVoice('ro-RO-AlinaNeural')}
                    className={`px-2 py-0.5 text-[11px] font-semibold rounded-full transition-all ${
                      selectedVoice === 'ro-RO-AlinaNeural' ? 'bg-white text-[#315D50] shadow-xs' : 'text-[#68736B]'
                    }`}
                  >
                    Alina
                  </button>
                  <button
                    onClick={() => setSelectedVoice('ro-RO-EmilNeural')}
                    className={`px-2 py-0.5 text-[11px] font-semibold rounded-full transition-all ${
                      selectedVoice === 'ro-RO-EmilNeural' ? 'bg-white text-[#315D50] shadow-xs' : 'text-[#68736B]'
                    }`}
                  >
                    Emil
                  </button>
                </div>
              </div>

              <button
                onClick={handleRegenerateAudio}
                disabled={isRegenerating}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-[#315D50] text-[#315D50] hover:bg-[#EDF2E9] text-xs font-semibold transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
                <span>{isRegenerating ? 'Se sintetizează...' : 'Regenerează Sunet Română'}</span>
              </button>
            </div>

            {notice && (
              <div className="p-2.5 bg-[#EDF2E9] border border-[#315D50]/20 rounded-md text-xs font-medium text-[#315D50] flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 shrink-0" />
                <span>{notice}</span>
              </div>
            )}

            {/* Below Player Tabs: Diagram | Timed Transcript | Notes | Quiz */}
            <div className="bg-white border border-[#DFE3D9] rounded-lg p-5 shadow-xs">
              <div className="flex items-center gap-2 border-b border-[#ECEEE7] pb-3 mb-4">
                <button
                  onClick={() => setActiveTab('diagram')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-all ${
                    activeTab === 'diagram' ? 'bg-[#315D50] text-white' : 'text-[#68736B] hover:text-[#25382F]'
                  }`}
                >
                  Diagramă UML
                </button>
                <button
                  onClick={() => setActiveTab('transcript')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-all ${
                    activeTab === 'transcript' ? 'bg-[#315D50] text-white' : 'text-[#68736B] hover:text-[#25382F]'
                  }`}
                >
                  Transcris Sincronizat
                </button>
                <button
                  onClick={() => setActiveTab('notes')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-all ${
                    activeTab === 'notes' ? 'bg-[#315D50] text-white' : 'text-[#68736B] hover:text-[#25382F]'
                  }`}
                >
                  Notițe Curs
                </button>
                <button
                  onClick={() => setActiveTab('quiz')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-all ${
                    activeTab === 'quiz' ? 'bg-[#315D50] text-white' : 'text-[#68736B] hover:text-[#25382F]'
                  }`}
                >
                  Test Grilă
                </button>
              </div>

              {/* Tab 1: UML Diagram */}
              {activeTab === 'diagram' && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-[#25382F] uppercase tracking-wide">
                    Arhitectură Vizuală a Conceptului
                  </h4>
                  <div className="p-4 bg-[#FAFAFA] border border-[#DFE3D9] rounded-lg overflow-x-auto">
                    <MermaidDiagram chart={lesson.mermaid_diagram || "graph LR\n  A[Problem] --> B[Solution]"} />
                  </div>
                </div>
              )}

              {/* Tab 2: Timed Transcript */}
              {activeTab === 'transcript' && (
                <div className="space-y-2.5">
                  <h4 className="text-xs font-bold text-[#25382F] uppercase tracking-wide mb-2">
                    Scene & Puncte Cheie (Apasă pe timestamp pentru a sări în audio)
                  </h4>
                  {activeTranscript.map((sc: any, idx: number) => (
                    <div 
                      key={idx}
                      onClick={() => {
                        if (sc.timestamp) {
                          const parts = sc.timestamp.split(':').map(Number);
                          const sec = (parts[0] || 0) * 60 + (parts[1] || 0);
                          handleSeek(sec);
                        }
                      }}
                      className="p-3 rounded-md bg-[#FAFAFA] hover:bg-[#EDF2E9] border border-[#DFE3D9] cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 rounded-full bg-[#315D50] text-white font-mono text-[10px] font-bold">
                          {sc.timestamp || `Scena ${idx + 1}`}
                        </span>
                        <span className="text-xs font-bold text-[#25382F]">
                          {sc.title || `Scena ${idx + 1}`}
                        </span>
                      </div>
                      <p className="text-xs text-[#68736B] leading-relaxed">
                        {sc.speaker || sc.text || ''}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 3: Notes */}
              {activeTab === 'notes' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-[#25382F] uppercase tracking-wide">
                      Notițe Personale
                    </h4>
                    {noteSavedFeedback && (
                      <span className="text-xs text-[#3E6650] font-semibold flex items-center gap-1">
                        <Check className="w-3 h-3" /> Salvat!
                      </span>
                    )}
                  </div>
                  <textarea
                    rows={6}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Scrie notițe din această lecție video..."
                    className="w-full p-3 text-xs bg-[#FAFAFA] border border-[#DFE3D9] rounded-md focus:border-[#315D50] outline-hidden text-[#25382F] resize-none"
                  />
                  <div className="flex justify-end">
                    <button
                      onClick={handleSaveNotes}
                      disabled={savingNotes}
                      className="px-4 py-1.5 rounded-full bg-[#315D50] hover:bg-[#23473C] text-white text-xs font-semibold"
                    >
                      {savingNotes ? 'Se salvează...' : 'Salvează Notițe'}
                    </button>
                  </div>
                </div>
              )}

              {/* Tab 4: Quiz */}
              {activeTab === 'quiz' && (
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-[#25382F] uppercase tracking-wide">
                    Evaluare Fixare Cunoștințe
                  </h4>
                  {quizzes.slice(0, 2).map((q, qIdx) => (
                    <div key={q.id} className="p-3 bg-[#FAFAFA] border border-[#DFE3D9] rounded-lg space-y-2">
                      <p className="text-xs font-bold text-[#25382F]">
                        {qIdx + 1}. {q.question}
                      </p>
                      <div className="space-y-1.5">
                        {q.options.map((opt, oIdx) => (
                          <button
                            key={oIdx}
                            onClick={() => setQuizAnswers({ ...quizAnswers, [q.id]: oIdx })}
                            className={`w-full text-left p-2 rounded-md text-xs transition-colors ${
                              quizAnswers[q.id] === oIdx
                                ? 'bg-[#315D50] text-white font-semibold'
                                : 'bg-white hover:bg-[#F8F7F2] text-[#25382F] border border-[#DFE3D9]'
                            }`}
                          >
                            {opt}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

            </div>

          </div>

          {/* Right Column: Syllabus List (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            
            <div className="bg-white border border-[#DFE3D9] rounded-lg p-4 shadow-xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-[#ECEEE7]">
                <h3 className="text-xs font-bold text-[#25382F] uppercase tracking-wide">
                  Programa Cursului ({allLessons.filter(l => l.completed).length}/{allLessons.length})
                </h3>
                <span className="text-xs font-bold text-[#315D50]">
                  {Math.round((allLessons.filter(l => l.completed).length / Math.max(1, allLessons.length)) * 100)}%
                </span>
              </div>

              <div className="space-y-1.5">
                {allLessons.map((lsn) => {
                  const isCurrent = lsn.id === lesson.id;
                  return (
                    <Link
                      key={lsn.id}
                      href={`/courses/${course.id}/video/${lsn.id}`}
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

          </div>

        </div>
      </div>
    </div>
  );
}

export default function VideoPlayerPage() {
  return (
    <Suspense fallback={
      <div className="max-w-[1200px] mx-auto px-4 py-8">
        <div className="h-[500px] bg-white rounded-lg border border-[#DFE3D9] animate-pulse" />
      </div>
    }>
      <VideoPlayerContent />
    </Suspense>
  );
}
