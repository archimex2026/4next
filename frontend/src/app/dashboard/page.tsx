'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowUpRight, Plus, Search } from 'lucide-react';
import { fetchCourses } from '@/lib/api';
import { Course } from '@/lib/types';
import CourseCard from '@/components/CourseCard';

export default function DashboardPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  useEffect(() => { fetchCourses().then(setCourses).finally(() => setLoading(false)); }, []);
  const visible = courses.filter(course => {
    const progress = course.completion_percentage || 0;
    const matchesFilter = filter === 'all' || (filter === 'started' && progress > 0 && progress < 100) || (filter === 'done' && progress === 100);
    const text = `${course.title} ${course.book_title || ''} ${course.author || ''}`;
    return matchesFilter && text.toLocaleLowerCase('ro').includes(query.toLocaleLowerCase('ro'));
  });

  return (
    <div className="study-shell library-page">
      <div className="section-heading library-heading"><div><span className="eyebrow">UN LOC PENTRU TOATE IDEILE TALE</span><h1>Biblioteca ta<span className="brand-dot">.</span></h1><p>Cursuri, cărți și notițe. Revino la ce te face curios.</p></div><Link href="/upload" className="study-button primary"><Plus size={18} />Adaugă material</Link></div>
      <div className="library-toolbar">
        <div className="library-filters" role="group" aria-label="Filtrează materialele">{[['all', 'Toate materialele'], ['started', 'În lucru'], ['done', 'Finalizate']].map(([value, label]) => <button key={value} onClick={() => setFilter(value)} aria-pressed={filter === value}>{label}{value === 'all' && <span>{courses.length}</span>}</button>)}</div>
        <label className="library-search"><Search size={17} /><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Caută un titlu sau un autor" aria-label="Caută în bibliotecă" /></label>
      </div>
      <div className="course-grid" aria-busy={loading}>
        {loading ? [0, 1, 2].map(i => <div key={i} className="course-skeleton animate-pulse" aria-label="Se încarcă materialele" />) : visible.length ? visible.map((course, index) => <CourseCard key={course.id} course={course} index={index} />) : <div className="empty-library"><Search size={25} /><h2>{query || filter !== 'all' ? 'Niciun material aici, deocamdată.' : 'Biblioteca ta începe cu un material.'}</h2><p>{query || filter !== 'all' ? 'Încearcă alt titlu sau schimbă filtrul.' : 'Adaugă un curs, o carte sau câteva notițe.'}</p><Link href="/upload" className="text-link">Adaugă material <ArrowUpRight size={17} /></Link></div>}
      </div>
    </div>
  );
}
