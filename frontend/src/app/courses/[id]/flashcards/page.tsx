'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { 
  Layers, ArrowLeft, ArrowRight, RotateCw, CheckCircle2, 
  Sparkles, Download, Shuffle, Undo2, Award, BookOpen, Clock,
  Check, ChevronRight
} from 'lucide-react';
import { fetchFlashcards, fetchCourse, toggleFlashcardMastery } from '@/lib/api';
import { Flashcard, Course } from '@/lib/types';

function FlashcardsContent() {
  const params = useParams();
  const courseId = params?.id as string;

  const [cards, setCards] = useState<Flashcard[]>([]);
  const [course, setCourse] = useState<Course | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  useEffect(() => {
    if (!courseId) return;
    setLoading(true);

    Promise.all([
      fetchFlashcards(courseId),
      fetchCourse(courseId)
    ])
      .then(([cardsData, courseData]) => {
        setCards(cardsData);
        setCourse(courseData);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [courseId]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        e.preventDefault();
        setIsFlipped((f) => !f);
      } else if (e.code === 'ArrowRight') {
        nextCard();
      } else if (e.code === 'ArrowLeft') {
        prevCard();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  const categories = ['All', ...Array.from(new Set(cards.map((c) => c.category || 'General')))];
  const filteredCards = selectedCategory === 'All' ? cards : cards.filter((c) => c.category === selectedCategory);
  const currentCard = filteredCards[currentIndex];

  const nextCard = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev + 1) % filteredCards.length);
  };

  const prevCard = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev - 1 + filteredCards.length) % filteredCards.length);
  };

  const handleMaster = async () => {
    if (!currentCard) return;
    try {
      const res = await toggleFlashcardMastery(currentCard.id);
      setCards((prev) =>
        prev.map((c) => (c.id === currentCard.id ? { ...c, mastered: res.mastered } : c))
      );
      nextCard();
    } catch (e) {
      console.error(e);
    }
  };

  const shuffleDeck = () => {
    setIsFlipped(false);
    setCards((prev) => [...prev].sort(() => Math.random() - 0.5));
    setCurrentIndex(0);
  };

  if (loading) {
    return (
      <div className="max-w-[1000px] mx-auto px-4 py-8">
        <div className="h-96 bg-white rounded-[8px] border border-[#E0E0E0] animate-pulse" />
      </div>
    );
  }

  const masteredCount = cards.filter((c) => c.mastered).length;
  const masteryPercentage = cards.length > 0 ? Math.round((masteredCount / cards.length) * 100) : 0;

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
              <span className="text-[#000000e6] font-semibold">Active Recall Flashcards</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#000000e6]">
              Knowledge Retention Flashcard Deck
            </h1>
            <p className="text-xs text-[#00000099] mt-0.5">
              Review core frameworks extracted from the publication. Press Spacebar to flip, arrow keys to navigate.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={shuffleDeck}
              className="b2c-btn-secondary py-1.5 px-3 text-xs"
            >
              <Shuffle className="w-3.5 h-3.5" />
              <span>Amestecă Cardurile</span>
            </button>

            <a
              href={`http://localhost:8000/api/export/course/${courseId}/anki`}
              download
              className="b2c-btn-secondary py-1.5 px-3 text-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Anki (.tsv)</span>
            </a>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-[1000px] mx-auto px-4 pt-6 space-y-6">
        {/* Progress & Category Filter Strip */}
        <div className="bg-white rounded-[8px] border border-[#E0E0E0] p-4 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          {/* Category Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => {
                  setSelectedCategory(cat);
                  setCurrentIndex(0);
                  setIsFlipped(false);
                }}
                className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                  selectedCategory === cat
                    ? 'bg-[#315D50] text-white shadow-2xs'
                    : 'bg-[#F8F7F2] text-[#000000e6] hover:bg-[#EBF3FA] hover:text-[#315D50]'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Mastery stats */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="text-right">
              <span className="text-xs font-semibold text-[#000000e6]">
                {masteredCount} of {cards.length} Mastered
              </span>
              <div className="w-32 h-1.5 bg-[#EDF3F8] rounded-full overflow-hidden mt-1">
                <div
                  className="h-full bg-[#3E6650] rounded-full transition-all duration-300"
                  style={{ width: `${masteryPercentage}%` }}
                />
              </div>
            </div>
            <span className="text-xs font-bold text-[#3E6650] bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              {masteryPercentage}%
            </span>
          </div>
        </div>

        {/* 3D Flip Flashcard Box */}
        {filteredCards.length > 0 && currentCard ? (
          <div className="space-y-6">
            <div 
              className="perspective-1000 w-full min-h-[320px] cursor-pointer" 
              onClick={() => setIsFlipped(!isFlipped)}
            >
              <div
                className={`relative w-full min-h-[320px] rounded-[8px] transition-transform duration-500 transform-style-3d shadow-sm hover:shadow-md ${
                  isFlipped ? 'rotate-y-180' : ''
                }`}
              >
                {/* Front Face: Question */}
                <div className="absolute inset-0 backface-hidden bg-white border border-[#E0E0E0] rounded-[8px] p-8 sm:p-12 flex flex-col justify-between">
                  <div className="flex items-center justify-between pb-4 border-b border-[#ECEEE7]">
                    <span className="px-2.5 py-1 rounded-[4px] text-[11px] font-bold bg-[#EBF3FA] text-[#315D50]">
                      {currentCard.category || 'Core Principle'}
                    </span>
                    <span className="text-xs font-mono text-[#00000099]">
                      Card {currentIndex + 1} of {filteredCards.length}
                    </span>
                  </div>

                  <div className="my-auto text-center py-6">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#00000099] block mb-2">
                      Question / Concept
                    </span>
                    <h2 className="text-xl sm:text-2xl font-bold text-[#000000e6] leading-snug">
                      {currentCard.question}
                    </h2>
                  </div>

                  <div className="flex items-center justify-between text-xs text-[#00000099] pt-4 border-t border-[#ECEEE7]">
                    <span>Click or tap Spacebar to reveal answer</span>
                    <RotateCw className="w-4 h-4 text-[#315D50]" />
                  </div>
                </div>

                {/* Back Face: Answer */}
                <div className="absolute inset-0 backface-hidden rotate-y-180 bg-[#223D33] text-white rounded-[8px] p-8 sm:p-12 flex flex-col justify-between border border-[#001D33] shadow-md">
                  <div className="flex items-center justify-between pb-4 border-b border-white/10">
                    <span className="px-2.5 py-1 rounded-[4px] text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      Validated Framework Answer
                    </span>
                    <span className="text-xs font-mono text-slate-300">
                      Card {currentIndex + 1} of {filteredCards.length}
                    </span>
                  </div>

                  <div className="my-auto text-center py-6">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-sky-300 block mb-2">
                      Core Explanation & Takeaway
                    </span>
                    <p className="text-base sm:text-lg text-slate-100 font-medium leading-relaxed max-w-xl mx-auto">
                      {currentCard.answer}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-300 pt-4 border-t border-white/10">
                    <span>Click again to return to question</span>
                    <RotateCw className="w-4 h-4 text-sky-400" />
                  </div>
                </div>
              </div>
            </div>

            {/* Controls Bar */}
            <div className="flex items-center justify-between bg-white rounded-xl border border-[#E2E8F0] p-4 shadow-xs">
              <button
                onClick={prevCard}
                className="b2c-btn-secondary py-2 px-4 text-xs"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Anterior</span>
              </button>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsFlipped(!isFlipped)}
                  className="b2c-btn-ghost py-2 px-4 text-xs"
                >
                  Întoarce Cardul (Space)
                </button>

                <button
                  onClick={handleMaster}
                  className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold transition-colors ${
                    currentCard.mastered
                      ? 'bg-[#3E6650] text-white hover:bg-[#045932]'
                      : 'border border-[#3E6650] text-[#3E6650] hover:bg-emerald-50'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{currentCard.mastered ? 'Asimilat ✓' : 'Marchează Asimilat'}</span>
                </button>
              </div>

              <button
                onClick={nextCard}
                className="b2c-btn-primary py-2 px-4 text-xs"
              >
                <span>Următor</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-[8px] border border-[#E0E0E0] p-8 text-center text-[#00000099]">
            No flashcards found for selected filter.
          </div>
        )}
      </div>
    </div>
  );
}

export default function FlashcardsPage() {
  return (
    <Suspense fallback={<div className="max-w-[1000px] mx-auto px-4 py-8"><div className="h-96 bg-white rounded-[8px] animate-pulse" /></div>}>
      <FlashcardsContent />
    </Suspense>
  );
}
