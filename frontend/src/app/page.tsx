'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, ArrowUpRight, BookOpen, Check, Headphones, Layers, Plus, Sprout } from 'lucide-react';
import { fetchCourses } from '@/lib/api';
import { Course } from '@/lib/types';
import CourseCard from '@/components/CourseCard';

export default function HomePage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { fetchCourses().then(setCourses).finally(() => setLoading(false)); }, []);
  const studyCourse = courses.find(course => (course.completion_percentage || 0) < 100) || courses[0];
  const studyPath = studyCourse ? `/courses/${studyCourse.id}` : '/dashboard';

  return (
    <div className="study-shell">
      <div className="welcome-line"><span><span className="tiny-sun" /> BINE AI VENIT ÎN SPAȚIUL TĂU</span><span>Curiozitatea e un început bun.</span></div>
      <section className="study-hero" aria-labelledby="welcome-title">
        <div className="hero-copy">
          <span className="eyebrow"><Sprout size={16} /> FIECARE IDEE MERITĂ ÎNȚELEASĂ</span>
          <h1 id="welcome-title">Fă loc ideilor.<br />Învață în <em>ritmul tău.</em></h1>
          <p>Un curs, câteva notițe sau o carte întreagă. Adună-le aici și explorează-le prin lecții, flashcarduri și întrebări care te pun pe gânduri.</p>
          <div className="hero-actions"><Link href="/upload" className="study-button primary"><Plus size={18} />Adaugă un material</Link><Link href={studyPath} className="text-link">Explorează un curs <ArrowUpRight size={17} /></Link></div>
          <span className="hero-footnote">PDF, EPUB, DOCX, TXT sau textul din notițele tale.</span>
        </div>
        <div className="notebook-scene">
          <span className="scene-orbit" aria-hidden="true" />
          <div className="study-notebook">
            <div className="notebook-top"><span>O IDEE PE ZI</span><BookOpen size={18} /></div>
            <span className="notebook-number">01</span>
            <h2>Înțelegi.<br />Exersezi.<br /><span>Îți rămâne.</span></h2>
            <div className="notebook-lines" aria-hidden="true" />
            <div className="notebook-bottom"><span>Materialele tale. Perspective noi.</span><ArrowUpRight size={18} /></div>
          </div>
          <Link href={studyCourse ? `${studyPath}/flashcards` : '/dashboard'} className="floating-note" aria-label="Explorează flashcardurile cursului">
            <span><Layers size={15} /> FLASHCARDURI</span><strong>Ce-ar fi să explici<br />ideea cu vorbele tale?</strong><span className="note-answer"><Check size={14} /> Așa începe înțelegerea.</span>
          </Link>
          <span className="handwritten">un pas mic, în fiecare zi <ArrowUpRight aria-hidden="true" size={25} /></span>
        </div>
      </section>
      <section className="study-modes" aria-label="Moduri de studiu">
        {[
          { icon: BookOpen, title: 'Pune ideile în ordine', text: 'Lecții scurte, explicații și scheme vizuale.', href: studyPath, tone: 'sage' },
          { icon: Layers, title: 'Vezi ce ți-a rămas', text: 'Flashcarduri și quizuri, fără presiune.', href: studyCourse ? `${studyPath}/flashcards` : '/dashboard', tone: 'peach' },
          { icon: Headphones, title: 'Schimbă perspectiva', text: 'Ascultă explicațiile sau urmărește o lecție.', href: studyPath, tone: 'lilac' },
        ].map(({ icon: Icon, title, text, href, tone }) => <Link href={href} key={title} className="study-mode"><span className={`mode-icon ${tone}`}><Icon size={23} strokeWidth={1.5} /></span><div><h2>{title}</h2><p>{text}</p></div><ArrowUpRight size={17} /></Link>)}
      </section>
      <section className="recent-section" aria-labelledby="recent-title">
        <div className="section-heading"><div><span className="eyebrow">DIN BIBLIOTECA TA</span><h2 id="recent-title">Următoarea pagină începe aici.</h2></div><Link href="/dashboard" className="text-link">Toate materialele <ArrowRight size={17} /></Link></div>
        <div className="course-grid" aria-busy={loading}>
          {loading ? [0, 1, 2].map(i => <div key={i} className="course-skeleton animate-pulse" aria-label="Se încarcă materialele" />) : courses.length ? courses.slice(0, 3).map((course, index) => <CourseCard key={course.id} course={course} index={index} />) : <div className="empty-library"><h3>Primul tău material își așteaptă locul.</h3><Link href="/upload" className="text-link">Adaugă un document <Plus size={16} /></Link></div>}
        </div>
      </section>
      <aside className="study-reminder"><Sprout className="reminder-mark" aria-hidden="true" size={35} /><p>Nu trebuie să înveți totul astăzi.<br /><strong>Doar să înțelegi un pic mai mult decât ieri.</strong></p><span>PAUZĂ. RESPIRĂ. CONTINUĂ.</span></aside>
    </div>
  );
}
