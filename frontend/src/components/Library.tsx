'use client';
import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Plus, Search, ArrowUpRight } from 'lucide-react';
import { Course } from '@/lib/types';
import { errorMessage, fetchCourses } from '@/lib/api';
import { useAuth } from './AuthProvider';
import CourseCard from './CourseCard';
import { Empty, ErrorNotice, Loading, LoginRequired, PageHeading } from './UI';
export default function Library({ isPublic = false, compact = false, initialQuery = '' }: {
    isPublic?: boolean;
    compact?: boolean;
    initialQuery?: string;
}) {
    const { user, loading: authLoading } = useAuth();
    const [courses, setCourses] = useState<Course[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [query, setQuery] = useState(initialQuery);
    const load = useCallback(() => fetchCourses(isPublic ? 'public' : 'mine').then(data => { setCourses(data); setError(''); }).catch(e => setError(errorMessage(e))).finally(() => setLoading(false)), [isPublic]);
    useEffect(() => { if (isPublic || user)
        void load(); }, [user, isPublic, load]);
    const filtered = courses.filter(course => `${course.title} ${course.book_title} ${course.author} ${course.overview} ${(course.keywords || []).join(' ')}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
    if (!isPublic && !user && !authLoading)
        return compact ? <div className="welcome-signin"><p>Materialele și progresul tău vor avea un loc aici.</p><Link className="text-button" href="/account">Creează-ți spațiul <ArrowUpRight size={16}/></Link></div> : <LoginRequired />;
    return <section>{compact ? <div className="section-heading"><div><span className="eyebrow">{isPublic ? 'DIN BIBLIOTECA COMUNITĂȚII' : 'DIN BIBLIOTECA TA'}</span><h2>{isPublic ? 'O idee bună se dă mai departe.' : 'Următoarea pagină începe aici.'}</h2></div><Link href={isPublic ? '/discover' : '/dashboard'} className="text-button">Toate materialele <ArrowUpRight size={16}/></Link></div> : <PageHeading eyebrow={isPublic ? 'BIBLIOTECA PUBLICĂ' : 'SPAȚIUL TĂU'} title={isPublic ? 'Idei care merită împărtășite.' : 'Ce învățăm astăzi?'} text={isPublic ? 'Explorează materialele publicate de comunitate. Consultă sursa și evaluează ce ți-a fost util.' : 'Materialele, notițele și progresul tău, adunate într-un singur loc.'}>{!isPublic && <Link href="/upload" className="button primary"><Plus size={17}/>Material nou</Link>}</PageHeading>}
    {!compact && <div className="search-field"><Search size={19}/><input type="search" aria-label="Caută în bibliotecă" value={query} onChange={e => setQuery(e.target.value)} placeholder="Caută un titlu, o idee, un autor…"/><span>{filtered.length} materiale</span></div>}
    {error ? <ErrorNotice message={error} retry={load}/> : loading || authLoading ? <Loading /> : filtered.length ? <div className="course-grid">{(compact ? filtered.slice(0, 3) : filtered).map((course, index) => <CourseCard key={course.id} course={course} index={index}/>)}</div> : <Empty title={query ? 'Niciun material cu aceste cuvinte.' : isPublic ? 'Biblioteca prinde contur.' : 'Primul tău material, primul pas.'} text={query ? 'Încearcă un alt titlu sau un termen mai simplu.' : isPublic ? 'Materialele publicate voluntar de utilizatori vor apărea aici.' : 'Adaugă un document sau notițele tale pentru lecții, exercițiu și întrebări din sursă.'} href={isPublic || query ? undefined : '/upload'}/>}
  </section>;
}
