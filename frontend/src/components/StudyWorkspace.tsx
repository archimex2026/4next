'use client';
import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, BookOpen, Check, Download, FileText, Globe2, Headphones, Layers3, LockKeyhole, MessageCircle, Play, Star } from 'lucide-react';
import { Course, Lesson, StudySource, Suggestions } from '@/lib/types';
import { downloadPdf, errorMessage, fetchCourse, fetchLesson, generateLessonAudio, getMediaUrl, mutate, request, saveLessonNotes, toggleLessonComplete } from '@/lib/api';
import { useAuth } from './AuthProvider';
import { Empty, ErrorNotice, Loading } from './UI';
import { Cards, Chat, Citations, Quiz, SourceReader } from './StudyTools';
import MermaidDiagram from './MermaidDiagram';
import StudyText from './StudyText';
import TrashCourseButton from './TrashCourseButton';
import GenerationProgress from './GenerationProgress';
type Tab = 'lessons' | 'source' | 'flashcards' | 'quiz' | 'chat';
export default function StudyWorkspace({ courseId, initialTab = 'lessons', initialLessonId }: {
    courseId: string;
    initialTab?: Tab;
    initialLessonId?: string;
}) {
    const router = useRouter();
    const { user } = useAuth();
    const [course, setCourse] = useState<Course | null>(null);
    const [source, setSource] = useState<StudySource | null>(null);
    const [suggestions, setSuggestions] = useState<Suggestions | null>(null);
    const [tab, setTab] = useState<Tab>(initialTab);
    const [lessonId, setLessonId] = useState(initialLessonId || '');
    const [focusPage, setFocusPage] = useState<number>();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const [pdfKind, setPdfKind] = useState('all');
    const [notice, setNotice] = useState('');
    const load = useCallback(() => Promise.all([fetchCourse(courseId), request<StudySource>(`/api/study/${courseId}/source`)]).then(([data, text]) => { setCourse(data); setSource(text); setError(''); void request<Suggestions>(`/api/study/${courseId}/suggestions`).then(setSuggestions).catch(() => setSuggestions(null)); }).catch(e => { setCourse(null); setSource(null); setError(errorMessage(e)); }).finally(() => setLoading(false)), [courseId]);
    useEffect(() => { void load(); }, [load, user?.id]);
    function openPage(page: number) { setFocusPage(page); setTab('source'); }
    async function visibility() { if (!course)
        return; setBusy(true); setError(''); try {
        await mutate(`/api/books/${course.book_id}/visibility`, { visibility: course.visibility === 'public' ? 'private' : 'public' }, 'PATCH');
        await load();
        setNotice(course.visibility === 'public' ? 'Materialul este acum privat.' : 'Materialul a fost publicat în bibliotecă.');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function rate(stars: number) { if (!course)
        return; setBusy(true); try {
        await mutate(`/api/books/${course.book_id}/rating`, { stars });
        await load();
        setNotice('Evaluarea ta a fost salvată.');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function exportPdf() { setBusy(true); try {
        await downloadPdf(courseId, pdfKind);
        setNotice('PDF-ul a fost descărcat.');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    if (loading)
        return <div className="page-shell"><Loading text="Deschidem spațiul de studiu…"/></div>;
    if (!course || !source)
        return <div className="page-shell"><Link className="back-link" href="/dashboard"><ArrowLeft size={16}/>Biblioteca mea</Link><ErrorNotice message={error || 'Materialul nu este disponibil.'} retry={load}/></div>;
    const lessons = course.levels?.flatMap(level => level.lessons) || [];
    const activeId = lessonId || lessons[0]?.id;
    const isOwner = course.is_owner || !!(user && course.owner_id === user.id);
    const visibilityLabel = course.visibility === 'public' ? 'Public' : 'Privat';
    const tabs: {
        key: Tab;
        label: string;
        icon: typeof BookOpen;
    }[] = [{ key: 'lessons', label: 'Lecții', icon: BookOpen }, { key: 'source', label: 'Sursa & evidențieri', icon: FileText }, { key: 'flashcards', label: 'Flashcarduri', icon: Layers3 }, { key: 'quiz', label: 'Verifică-te', icon: Check }, { key: 'chat', label: 'Întreabă materialul', icon: MessageCircle }];
    return <div className="page-shell workspace"><header className="workspace-header"><Link className="back-link" href={isOwner ? '/dashboard' : '/discover'}><ArrowLeft size={15}/>Înapoi la bibliotecă</Link><div className="workspace-title"><div><span className="eyebrow">SPAȚIU DE STUDIU / {source.language.toUpperCase()}</span><h1>{course.book_title || course.book?.title || course.title}</h1><p lang={source.language}>{course.overview}</p></div><span className="status-badge">{visibilityLabel}</span></div><div className="workspace-meta"><span><BookOpen size={14}/>{lessons.length} lecții</span><span><FileText size={14}/>{source.pages.length} pagini / secțiuni</span><span>{source.study_minutes} min / sesiune</span><span title="Materialul este prelucrat în limba sursei.">Limba documentului: {source.language.toUpperCase()}</span><span title={source.generation_mode === 'extractive' ? 'Organizare și fragmente extrase direct din sursă, fără generare printr-un model extern.' : 'Explicații AI verificate față de fragmentele citate. Verifică întotdeauna sursa.'}>{source.generation_mode === 'extractive' ? 'Din sursă · extragere locală' : source.generation_mode === 'ai_grounded' ? 'Explicații AI · cu surse' : source.generation_mode === 'mixed' ? 'Explicații AI și extrase' : 'Material preexistent'}</span></div></header><div className="workspace-toolbar">{isOwner && <button className="button secondary" onClick={visibility} disabled={busy}>{course.visibility === 'public' ? <LockKeyhole size={15}/> : <Globe2 size={15}/>} {course.visibility === 'public' ? 'Fă privat' : 'Publică materialul'}</button>}<label className="sr-only" htmlFor="pdf-kind">Conținutul exportului PDF</label><select id="pdf-kind" value={pdfKind} onChange={e => setPdfKind(e.target.value)}><option value="all">PDF · tot materialul</option><option value="source">PDF · sursa</option><option value="lessons">PDF · lecțiile</option><option value="flashcards">PDF · flashcardurile</option><option value="quiz">PDF · quizul</option></select><button className="button secondary" onClick={exportPdf} disabled={busy}><Download size={15}/>Descarcă PDF</button>{isOwner && <TrashCourseButton courseId={course.id} title={course.book_title || course.title} onDeleted={() => router.push('/trash')}/>} {course.visibility === 'public' && <div className="rating" aria-label="Evaluează materialul">{[1, 2, 3, 4, 5].map(stars => <button key={stars} aria-label={`Evaluează cu ${stars} ${stars === 1 ? 'stea' : 'stele'}`} disabled={!user || busy || isOwner} onClick={() => rate(stars)} title={user ? `${stars} stele` : 'Autentifică-te pentru a evalua'}><Star size={19} fill={stars <= Math.round(course.rating_average || 0) ? 'currentColor' : 'none'}/></button>)}<span>{(course.rating_average || 0).toFixed(1)} · {course.rating_count || 0} voturi</span></div>}</div>{isOwner && course.visibility !== 'public' && <p className="small muted" style={{ marginBottom: 16 }}>Privat pentru tine și clasele cărora îl oferi. Publică doar materiale pe care ai dreptul să le distribui.</p>}{!source.pages.length && <p className="notice">Acest material preexistent nu are sursa originală salvată. Reîncarcă documentul pentru chat, evidențieri și exportul sursei; lecțiile existente rămân disponibile.</p>}{error && <ErrorNotice message={error}/>} {notice && <p className="notice" role="status">{notice}</p>}{source.generation_progress ? <GenerationProgress courseId={courseId} progress={source.generation_progress} isOwner={isOwner} onProgress={load} onPage={openPage}/> : <p className="notice">Această sesiune de {source.study_minutes} minute este o selecție de idei, nu o acoperire completă. Sursa și chatul au acces la toate paginile încărcate.</p>}{source.generation_mode === 'extractive' && <p className="notice" role="status">Explicațiile AI nu au fost disponibile sau nu au trecut verificarea. Mai jos sunt doar fragmente pentru lectură, nu o lecție explicată de AI. Poți reîncărca materialul pentru o nouă încercare.</p>}<nav className="workspace-tabs" aria-label="Instrumente de studiu">{tabs.map(({ key, label, icon: Icon }) => <button key={key} className={tab === key ? 'active' : ''} aria-current={tab === key ? 'page' : undefined} onClick={() => setTab(key)}><Icon size={17}/>{label}</button>)}</nav><section className="workspace-content">{tab === 'lessons' && (lessons.length ? <div className="study-layout"><aside className="lesson-nav"><h3>CUPRINSUL TĂU</h3>{lessons.map((lesson, index) => <button key={lesson.id} className={activeId === lesson.id ? 'active' : ''} onClick={() => setLessonId(lesson.id)}><span>{String(index + 1).padStart(2, '0')}</span><span lang={source.language}>{lesson.title}</span>{lesson.completed && <Check size={13}/>}</button>)}</aside><LessonReader key={activeId} lessonId={activeId} language={source.language} isOwner={isOwner} onPage={openPage} onProgress={load}/></div> : <Empty title="Nu există lecții în acest material." text="Verifică sursa sau încearcă un document mai detaliat."/>)}{tab === 'source' && <SourceReader courseId={courseId} source={source} focusPage={focusPage}/>} {tab === 'flashcards' && <Cards courseId={courseId} language={source.language} onPage={openPage}/>} {tab === 'quiz' && <Quiz courseId={courseId} language={source.language} onPage={openPage}/>} {tab === 'chat' && <Chat courseId={courseId} source={source} suggestions={suggestions} onPage={openPage}/>}</section></div>;
}
function LessonReader({ lessonId, language, isOwner, onPage, onProgress }: {
    lessonId: string;
    language: string;
    isOwner: boolean;
    onPage: (page: number) => void;
    onProgress: () => Promise<void>;
}) {
    const { user } = useAuth();
    const [lesson, setLesson] = useState<Lesson | null>(null);
    const [notes, setNotes] = useState('');
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');
    const [busy, setBusy] = useState(false);
    const load = useCallback(() => fetchLesson(lessonId).then(data => { setLesson(data); setNotes(data.notes || ''); setError(''); }).catch(e => setError(errorMessage(e))), [lessonId]);
    useEffect(() => { void load(); }, [load]);
    async function complete() { setBusy(true); try {
        const result = await toggleLessonComplete(lessonId);
        setLesson(current => current ? { ...current, completed: result.completed } : current);
        await onProgress();
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function save() { setBusy(true); try {
        await saveLessonNotes(lessonId, notes);
        setNotice('Notițele tale au fost salvate.');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function audio() { setBusy(true); setNotice('Generăm explicația audio. Poate dura câteva momente.'); try {
        const data = await generateLessonAudio(lessonId, undefined, language);
        setLesson(data);
        setNotice('Explicația audio este pregătită.');
    }
    catch (e) {
        setError(errorMessage(e));
        setNotice('');
    }
    finally {
        setBusy(false);
    } }
    if (!lesson)
        return error ? <ErrorNotice message={error} retry={load}/> : <Loading text="Se deschide lecția…"/>;
    const audioUrl = lesson.active_audio_url || lesson.audio_url;
    return <article className="lesson-article">{error && <ErrorNotice message={error}/>}<div lang={language}><span className="eyebrow">LECTURĂ CU SENS</span><h2>{lesson.title}</h2><StudyText text={lesson.long_explanation || lesson.short_summary}/>{[['Idei de reținut', lesson.key_ideas], ['Exemple din material', lesson.examples], ['Aplică ce ai învățat', lesson.action_items]].map(([title, items]) => Array.isArray(items) && items.length ? <section key={String(title)}><h3>{title as string}</h3><ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul></section> : null)}{lesson.mermaid_diagram && <MermaidDiagram chart={lesson.mermaid_diagram}/>}<Citations citations={lesson.source_citations} onPage={onPage}/></div><div className="audio-section"><div className="row spaced wrap"><span className="inline small"><Headphones size={18}/>O altă perspectivă: ascultă lecția</span>{isOwner && ['ro', 'en'].includes(language) && !audioUrl && <button className="text-button" disabled={busy} onClick={audio}><Play size={15}/>Generează explicația audio</button>}</div>{audioUrl ? <audio controls src={getMediaUrl(audioUrl)} preload="metadata" aria-label={`Explicație audio: ${lesson.title}`}/> : <p className="small muted" style={{ marginTop: 12 }}>{['ro', 'en'].includes(language) ? 'Audio este opțional și se generează la cerere de către proprietarul materialului.' : 'Pentru această limbă studiul este disponibil în format text. Audio nu este încă disponibil.'}</p>}{lesson.video_url && <><h3>Explicație video</h3><video className="media-player" controls preload="metadata" src={getMediaUrl(lesson.video_url)}/></>}</div>{notice && <p className="notice" role="status">{notice}</p>}{user ? <div className="lesson-note"><label htmlFor={`notes-${lessonId}`}>Notițele tale</label><textarea id={`notes-${lessonId}`} rows={4} value={notes} maxLength={20000} onChange={e => setNotes(e.target.value)} placeholder="Cum ai explica ideea cu vorbele tale?"/><div className="note-actions"><button className="button secondary" onClick={save} disabled={busy}>Salvează notițele</button><button className="button primary" onClick={complete} disabled={busy}><Check size={16}/>{lesson.completed ? 'Marchează pentru reluat' : 'Am parcurs lecția'}</button></div></div> : <p className="small muted" style={{ marginTop: 24 }}><Link href="/account" className="text-button">Intră în cont pentru notițe și progres <ArrowLeft size={14}/></Link></p>}</article>;
}
