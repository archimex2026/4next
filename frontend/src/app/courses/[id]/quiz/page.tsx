'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { 
  Award, ArrowLeft, CheckCircle2, XCircle, RotateCcw, 
  Sparkles, Check, ChevronRight, HelpCircle, BookOpen,
  Share2, Download, ExternalLink, ShieldCheck
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { fetchQuizzes, fetchCourse, submitQuiz } from '@/lib/api';
import { QuizQuestion, Course, QuizResult } from '@/lib/types';

function QuizAssessmentContent() {
  const params = useParams();
  const courseId = params?.id as string;

  const [quizzes, setQuizzes] = useState<QuizQuestion[]>([]);
  const [course, setCourse] = useState<Course | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [copiedCert, setCopiedCert] = useState(false);

  useEffect(() => {
    if (!courseId) return;
    setLoading(true);

    Promise.all([
      fetchQuizzes(courseId),
      fetchCourse(courseId)
    ])
      .then(([qData, cData]) => {
        setQuizzes(qData);
        setCourse(cData);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [courseId]);

  const selectOption = (quizId: string, optionIndex: number) => {
    if (result) return;
    setSelectedAnswers((prev) => ({
      ...prev,
      [quizId]: optionIndex,
    }));
  };

  const handleSubmit = async () => {
    if (Object.keys(selectedAnswers).length < quizzes.length) {
      if (!confirm('You have unanswered questions. Are you sure you want to submit your exam now?')) {
        return;
      }
    }

    setSubmitting(true);
    try {
      const res = await submitQuiz(courseId, selectedAnswers);
      setResult(res);

      if (res.passed) {
        confetti({
          particleCount: 140,
          spread: 80,
          origin: { y: 0.55 },
        });
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetake = () => {
    setResult(null);
    setSelectedAnswers({});
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleShareCertificate = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      setCopiedCert(true);
      setTimeout(() => setCopiedCert(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="max-w-[1000px] mx-auto px-4 py-8">
        <div className="h-96 bg-white rounded-[8px] border border-[#E0E0E0] animate-pulse" />
      </div>
    );
  }

  const answeredCount = Object.keys(selectedAnswers).length;

  return (
    <div className="min-h-screen bg-[#F8F7F2] pb-16">
      {/* Top Header */}
      <div className="bg-white border-b border-[#E0E0E0]">
        <div className="max-w-[1000px] mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs text-[#00000099] mb-1">
              <Link href={`/courses/${courseId}`} className="text-[#315D50] hover:underline flex items-center gap-1 font-semibold">
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>{course?.title || 'Back to Course'}</span>
              </Link>
              <span>/</span>
              <span className="text-[#000000e6] font-semibold">Skill Assessment</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-[#EDF2E9] text-[#315D50] text-[10px] font-bold uppercase tracking-wider">
                4next • Evaluare Cunoștințe
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#0F172A] mt-1">
              Ce ai reținut?
            </h1>
            <p className="text-xs text-[#64748B] mt-0.5">
              Răspunde în ritmul tău. La final vezi explicațiile și conceptele la care merită să revii.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-[#EDF2E9] text-[#315D50]">
              {answeredCount} din {quizzes.length} Răspunse
            </span>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-[1000px] mx-auto px-4 pt-6 space-y-6">
        {/* Certificate Display if Passed */}
        {result && result.passed && (
          <div className="bg-white rounded-xl border-2 border-[#315D50] p-8 shadow-lg text-center space-y-6 relative overflow-hidden">
            {/* Top Certificate Header */}
            <div className="flex items-center justify-between pb-4 border-b border-[#E2E8F0]">
              <div className="flex items-center gap-2.5 text-left">
                <div className="w-8 h-8 rounded-lg bg-[#315D50] text-white font-black text-sm flex items-center justify-center shadow-xs">
                  4N
                </div>
                <div>
                  <span className="text-xs font-bold tracking-tight text-[#0F172A] block leading-none">
                    4NEXT
                  </span>
                  <span className="text-[9px] text-[#315D50] font-semibold uppercase tracking-wider">
                    Fișă de progres
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-[#3E6650] font-bold">
                <ShieldCheck className="w-4 h-4" />
                <span>Prag de 70% atins</span>
              </div>
            </div>

            {/* Certificate Body */}
            <div className="py-6 space-y-3">
              <span className="text-xs font-semibold text-[#64748B] uppercase tracking-wider block">
                Felicitări pentru încă un pas!
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-[#0F172A]">
                Ai pus ideile în practică.
              </h2>
              <p className="text-xs text-[#64748B]">
                Ai încheiat cu succes recapitularea pentru
              </p>
              <h3 className="text-lg sm:text-xl font-bold text-[#315D50]">
                {course?.title}
              </h3>
              <p className="text-xs text-[#64748B]">
                Sintetizat din opera autorului {course?.author} • Scor Obținut: {result.percentage}% ({result.score}/{result.total})
              </p>
            </div>

            {/* Actions: Save / Share Certificate */}
            <div className="pt-4 border-t border-[#E2E8F0] flex flex-wrap items-center justify-center gap-3">
              <button
                onClick={handleShareCertificate}
                className="b2c-btn-primary py-2 px-5 text-xs shadow-xs"
              >
                <Award className="w-4 h-4" />
                <span>{copiedCert ? 'Link Copiat!' : 'Distribuie Certificatul'}</span>
              </button>

              <Link
                href={`/courses/${courseId}`}
                className="b2c-btn-secondary py-2 px-4 text-xs"
              >
                Înapoi la Curriculum
              </Link>
            </div>
          </div>
        )}

        {/* Failed Banner */}
        {result && !result.passed && (
          <div className="bg-white rounded-[8px] border border-rose-300 p-6 shadow-xs text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <XCircle className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-[#000000e6]">
              Assessment Incomplete: Score {result.percentage}%
            </h2>
            <p className="text-xs text-[#00000099] max-w-md mx-auto">
              You scored {result.score} out of {result.total} questions correct. A score of 70% is required to earn the Certificate of Completion.
            </p>
            <div className="pt-2 flex justify-center gap-3">
              <button
                onClick={handleRetake}
                className="b2c-btn-primary py-2 px-4 text-xs"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reia Chestionarul</span>
              </button>
            </div>
          </div>
        )}

        {/* Questions List */}
        <div className="space-y-4">
          {quizzes.map((q, qIndex) => {
            const selectedOption = selectedAnswers[q.id];
            const feedbackItem = result?.feedback.find((f) => f.quiz_id === q.id);

            return (
              <div key={q.id} className="bg-white rounded-[8px] border border-[#E0E0E0] p-6 shadow-xs space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#315D50]">
                    Question {qIndex + 1} of {quizzes.length}
                  </span>

                  {feedbackItem && (
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-bold flex items-center gap-1 ${
                        feedbackItem.is_correct
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {feedbackItem.is_correct ? <Check className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      <span>{feedbackItem.is_correct ? 'Correct' : 'Incorrect'}</span>
                    </span>
                  )}
                </div>

                <h3 className="text-sm sm:text-base font-bold text-[#000000e6] leading-snug">
                  {q.question}
                </h3>

                {/* Options Selection */}
                <div className="space-y-2 pt-1">
                  {q.options.map((opt, optIndex) => {
                    const isSelected = selectedOption === optIndex;
                    const isCorrect = feedbackItem && feedbackItem.correct_index === optIndex;
                    const isWrongSelection = feedbackItem && isSelected && !feedbackItem.is_correct;

                    let optionClass = 'bg-white border-[#E0E0E0] text-[#000000e6] hover:bg-[#F8F7F2]';
                    if (isSelected && !result) {
                      optionClass = 'bg-[#EBF3FA] border-[#315D50] text-[#315D50] font-semibold';
                    } else if (isCorrect) {
                      optionClass = 'bg-emerald-50 border-emerald-500 text-emerald-900 font-bold';
                    } else if (isWrongSelection) {
                      optionClass = 'bg-rose-50 border-rose-400 text-rose-900';
                    }

                    return (
                      <button
                        key={optIndex}
                        onClick={() => selectOption(q.id, optIndex)}
                        disabled={!!result}
                        className={`w-full text-left p-3 rounded-[6px] border text-xs transition-all flex items-center justify-between ${optionClass}`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-5 h-5 rounded-full border flex items-center justify-center font-bold text-[10px] shrink-0 ${
                            isSelected ? 'border-[#315D50] bg-[#315D50] text-white' : 'border-[#CBD5E1] text-[#666666]'
                          }`}>
                            {String.fromCharCode(65 + optIndex)}
                          </div>
                          <span>{opt}</span>
                        </div>
                        {isCorrect && <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />}
                        {isWrongSelection && <XCircle className="w-4 h-4 text-rose-500 shrink-0" />}
                      </button>
                    );
                  })}
                </div>

                {/* Explanation if Submitted */}
                {feedbackItem && (
                  <div className="mt-3 p-3.5 rounded-[6px] bg-[#F8FAFC] border border-[#E0E0E0] text-xs text-[#000000e6] leading-relaxed">
                    <span className="font-bold text-[#315D50] block mb-1">Concept Rationale:</span>
                    {feedbackItem.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Submit Actions */}
        {!result && (
          <div className="bg-white rounded-[8px] border border-[#E0E0E0] p-6 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-[#000000e6]">Ready to evaluate your answers?</h4>
              <p className="text-xs text-[#00000099] mt-0.5">
                Ensure you have responded to all {quizzes.length} questions before submitting.
              </p>
            </div>

            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="b2c-btn-primary py-2.5 px-6 text-xs w-full sm:w-auto"
            >
              <Sparkles className="w-4 h-4 fill-white" />
              <span>{submitting ? 'Se evaluează răspunsurile...' : 'Trimite Răspunsurile'}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function QuizAssessmentPage() {
  return (
    <Suspense fallback={<div className="max-w-[1000px] mx-auto px-4 py-8"><div className="h-96 bg-white rounded-[8px] animate-pulse" /></div>}>
      <QuizAssessmentContent />
    </Suspense>
  );
}
