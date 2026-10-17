'use client';
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, BookmarkPlus, Check, ExternalLink, RotateCcw, Send, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { ChatAnswer, Citation, Flashcard, Highlight, QuizQuestion, QuizResult, StudySource, Suggestions } from '@/lib/types';
import { errorMessage, fetchFlashcards, fetchQuizzes, mutate, request, submitQuiz, toggleFlashcardMastery } from '@/lib/api';
import { useAuth } from './AuthProvider';
import { Empty, ErrorNotice, Loading } from './UI';
export function Citations({ citations, onPage }: {
    citations?: Citation[];
    onPage: (page: number) => void;
}) {
    if (!citations?.length)
        return null;
    return <div className="source-citations">{citations.map((citation, index) => <button key={index} className="citation-button" onClick={() => onPage(citation.page)}><strong>{citation.source_title || 'Sursa'} · pagina {citation.page}</strong>{citation.text}</button>)}</div>;
}
function markedText(text: string, highlights: Highlight[]) {
    const codepoints = Array.from(text);
    const sorted = [...highlights].sort((a, b) => a.start_offset - b.start_offset);
    const parts: React.ReactNode[] = [];
    let offset = 0;
    sorted.forEach(item => { const start = Math.max(offset, item.start_offset); const end = Math.min(codepoints.length, item.end_offset); if (end <= start)
        return; parts.push(codepoints.slice(offset, start).join('')); parts.push(<mark key={item.id}>{codepoints.slice(start, end).join('')}</mark>); offset = end; });
    parts.push(codepoints.slice(offset).join(''));
    return parts;
}
export function SourceReader({ courseId, source, focusPage }: {
    courseId: string;
    source: StudySource;
    focusPage?: number;
}) {
    const { user } = useAuth();
    const [highlights, setHighlights] = useState<Highlight[]>([]);
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const [selection, setSelection] = useState<{
        page: number;
        start_offset: number;
        end_offset: number;
        text: string;
    } | null>(null);
    const load = useCallback(() => request<Highlight[]>(`/api/study/${courseId}/highlights`).then(setHighlights).catch(e => setError(errorMessage(e))), [courseId]);
    useEffect(() => { if (user)
        void load(); }, [user, load]);
    useEffect(() => { if (focusPage)
        document.getElementById(`source-page-${focusPage}`)?.scrollIntoView({ block: 'center', behavior: 'smooth' }); }, [focusPage]);
    function selectText(page: number, element: HTMLDivElement) { const selected = window.getSelection(); if (!selected || selected.isCollapsed || !selected.rangeCount) {
        setSelection(null);
        return;
    } const range = selected.getRangeAt(0); if (!element.contains(range.commonAncestorContainer)) {
        setSelection(null);
        return;
    } const before = range.cloneRange(); before.selectNodeContents(element); before.setEnd(range.startContainer, range.startOffset); const text = selected.toString(); if (text.trim())
        setSelection({ page, start_offset: Array.from(before.toString()).length, end_offset: Array.from(before.toString()).length + Array.from(text).length, text }); }
    async function save() { if (!selection)
        return; setBusy(true); setError(''); try {
        await mutate(`/api/study/${courseId}/highlights`, { ...selection, color: 'yellow' });
        await load();
        setSelection(null);
        window.getSelection()?.removeAllRanges();
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function remove(id: string) { try {
        await mutate(`/api/study/${courseId}/highlights/${id}`, undefined, 'DELETE');
        await load();
    }
    catch (e) {
        setError(errorMessage(e));
    } }
    return <div className="source-layout"><div>{source.pages.map(page => <article key={page.page} id={`source-page-${page.page}`} className="source-page"><span>{source.page_kind === 'section' ? 'SECȚIUNEA' : 'PAGINA'} {page.page} · {source.title}</span><div lang={source.language} className="source-text" onPointerUp={e => selectText(page.page, e.currentTarget)} onKeyUp={e => selectText(page.page, e.currentTarget)} tabIndex={0} aria-label={`Textul paginii ${page.page}`}>{markedText(page.text, highlights.filter(item => item.page === page.page))}</div></article>)}</div><aside className="panel source-sidebar"><h2>Firul ideilor.</h2><div className="keyword-list">{source.keywords.map(keyword => <span key={keyword}>{keyword}</span>)}</div><p className="source-legend">Concepte extrase din materialul tău.</p>{!!source.focus_keywords?.length && <div style={{ marginTop: 20 }}><span className="eyebrow">FOCUSUL ALES</span><p className="small muted" style={{ marginTop: 8 }}>{source.focus_keywords.join(', ')}</p></div>}<div className="divider"/><h3>De păstrat</h3><p className="small muted">Selectează o propoziție din sursă, apoi salvează evidențierea.</p>{user ? <><button className="button secondary" disabled={!selection || busy} onClick={save} style={{ marginTop: 16 }}><BookmarkPlus size={16}/>{busy ? 'Se salvează…' : 'Evidențiază selecția'}</button>{selection && <p className="small muted" style={{ marginTop: 10 }}>Pagina {selection.page} · {selection.text.length} caractere selectate</p>}<div className="highlight-list">{highlights.map(item => <div key={item.id} className="highlight-item"><div className="row spaced"><strong>Pagina {item.page}</strong><button aria-label="Șterge evidențierea" className="icon-button" onClick={() => remove(item.id)}><Trash2 size={14}/></button></div><p>{item.text}</p></div>)}</div></> : <Link className="text-button" href="/account">Intră în cont pentru evidențieri <ArrowRight size={15}/></Link>}{error && <ErrorNotice message={error}/>}</aside></div>;
}
export function Cards({ courseId, language, onPage }: {
    courseId: string;
    language: string;
    onPage: (page: number) => void;
}) {
    const { user } = useAuth();
    const [cards, setCards] = useState<Flashcard[]>([]);
    const [index, setIndex] = useState(0);
    const [flipped, setFlipped] = useState(false);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const load = useCallback(() => fetchFlashcards(courseId).then(data => { setCards(data); setError(''); }).catch(e => setError(errorMessage(e))).finally(() => setLoading(false)), [courseId]);
    useEffect(() => { void load(); }, [load]);
    async function master() { if (!cards[index])
        return; setBusy(true); try {
        const result = await toggleFlashcardMastery(cards[index].id);
        setCards(items => items.map((item, i) => i === index ? { ...item, mastered: result.mastered } : item));
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    if (loading)
        return <Loading />;
    if (!cards.length)
        return error ? <ErrorNotice message={error} retry={load}/> : <Empty title="Niciun flashcard în acest material." text="Adaugă un document cu mai mult conținut pentru a putea extrage întrebări utile."/>;
    const card = cards[index];
    return <div className="flashcard-shell">{error && <ErrorNotice message={error}/>}<div className="row spaced" style={{ marginBottom: 18 }}><span className="eyebrow">RECAPITULARE ACTIVĂ</span><span className="small muted">{cards.filter(item => item.mastered).length} / {cards.length} stăpânite</span></div><button lang={language} className={`flashcard ${flipped ? 'answer' : ''}`} onClick={() => setFlipped(!flipped)} aria-label={flipped ? 'Ascunde răspunsul' : 'Arată răspunsul'}><span className="eyebrow">{flipped ? 'RĂSPUNS' : 'ÎNTREBARE'} {index + 1} / {cards.length}</span>{flipped ? <p>{card.answer}</p> : <h2>{card.question}</h2>}<span className="small muted">{flipped ? 'Apasă pentru întrebare' : 'Gândește-te la răspuns, apoi întoarce cardul.'}</span></button><div className="flashcard-controls"><button className="button secondary" disabled={index === 0} onClick={() => { setIndex(index - 1); setFlipped(false); }}><ArrowLeft size={16}/>Înapoi</button>{user && <button className="button secondary" onClick={master} disabled={busy}><Check size={16}/>{card.mastered ? 'Mai exersez' : 'Am înțeles'}</button>}<button className="button secondary" disabled={index === cards.length - 1} onClick={() => { setIndex(index + 1); setFlipped(false); }}>Următorul<ArrowRight size={16}/></button></div>{flipped && <Citations citations={card.source_citations} onPage={onPage}/>}</div>;
}
export function Quiz({ courseId, language, onPage }: {
    courseId: string;
    language: string;
    onPage: (page: number) => void;
}) {
    const { user } = useAuth();
    const [questions, setQuestions] = useState<QuizQuestion[]>([]);
    const [answers, setAnswers] = useState<Record<string, number>>({});
    const [result, setResult] = useState<QuizResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const load = useCallback(() => fetchQuizzes(courseId).then(data => { setQuestions(data); setError(''); }).catch(e => setError(errorMessage(e))).finally(() => setLoading(false)), [courseId]);
    useEffect(() => { void load(); }, [load]);
    async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(''); try {
        setResult(await submitQuiz(courseId, answers));
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    if (loading)
        return <Loading />;
    if (!questions.length)
        return error ? <ErrorNotice message={error} retry={load}/> : <Empty title="Niciun quiz în acest material." text="Un material mai amplu oferă context pentru exerciții de verificare."/>;
    return <div className="quiz-shell">{error && <ErrorNotice message={error}/>}<p className="small muted" style={{ marginBottom: 20 }}>Oprește-te, amintește-ți, verifică. {questions.length} întrebări din sursa ta.</p>{result && <div className="quiz-result" role="status"><strong>{result.score} / {result.total}</strong><span>{result.percentage}% răspunsuri corecte</span><p className="small muted">Revino la explicațiile de mai jos și verifică fragmentele din sursă.</p><button className="text-button" onClick={() => { setResult(null); setAnswers({}); }}><RotateCcw size={15}/>Încearcă din nou</button></div>}<form onSubmit={submit}><div lang={language}>{questions.map((question, index) => { const feedback = result?.feedback.find(item => item.quiz_id === question.id); return <article className="quiz-question" key={question.id}><h2>{index + 1}. {question.question}</h2><fieldset className="quiz-options" disabled={!!result} style={{ border: 0, padding: 0 }}><legend className="sr-only">{question.question}</legend>{question.options.map((option, i) => <label key={i} className={`quiz-option ${feedback?.correct_index === i ? 'correct' : feedback?.selected_index === i && !feedback.is_correct ? 'wrong' : ''}`}><input type="radio" name={question.id} required checked={answers[question.id] === i} onChange={() => setAnswers({ ...answers, [question.id]: i })}/>{option}</label>)}</fieldset>{feedback && <><p className="quiz-feedback">{feedback.explanation}</p><Citations citations={question.source_citations} onPage={onPage}/></>}</article>; })}</div>{!result && (user ? <button className="button primary quiz-submit" disabled={busy || Object.keys(answers).length < questions.length}>{busy ? 'Se verifică…' : 'Verifică răspunsurile'}<Check size={17}/></button> : <Link href="/account" className="text-button">Intră în cont pentru a verifica și salva rezultatul <ArrowRight size={15}/></Link>)}</form></div>;
}
export function SuggestionsPanel({ suggestions, onAsk }: {
    suggestions: Suggestions | null;
    onAsk?: (term: string) => void;
}) { return <div className="suggestion-list">{suggestions?.concepts?.map(item => <div className="suggestion-item" key={item.term}><h3>{item.term}</h3><p>{item.reason}</p>{onAsk && <button className="text-button concept-button" onClick={() => onAsk(item.term)}>Întreabă despre concept <ArrowRight size={13}/></button>}<div className="row wrap"><Link href={`/discover?q=${encodeURIComponent(item.query || item.term)}`} className="text-button">În bibliotecă <ArrowRight size={12}/></Link><a href={`https://www.google.com/search?q=${encodeURIComponent(item.query || item.term)}`} target="_blank" rel="noopener noreferrer" className="text-button">Pe Google <ExternalLink size={12}/></a></div></div>)}{!suggestions?.concepts?.length && <p className="small muted">Sugestiile vor apărea când sursa are suficiente concepte identificabile.</p>}</div>; }
export function Chat({ courseId, source, suggestions, onPage }: {
    courseId: string;
    source: StudySource;
    suggestions: Suggestions | null;
    onPage: (page: number) => void;
}) {
    const { user } = useAuth();
    const [message, setMessage] = useState('');
    const [history, setHistory] = useState<{
        question: string;
        response: ChatAnswer;
    }[]>([]);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const bottomRef = useRef<HTMLDivElement>(null);
    useEffect(() => { bottomRef.current?.scrollIntoView({ block: 'nearest' }); }, [history, busy]);
    async function send(event: FormEvent) { event.preventDefault(); if (!message.trim())
        return; const question = message.trim(); setBusy(true); setError(''); try {
        const response = await mutate<ChatAnswer>(`/api/study/${courseId}/chat`, { message: question, previous_question: history.at(-1)?.question });
        setHistory(items => [...items, { question, response }]);
        setMessage('');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    const questionPrefix: Record<string, string> = { ro: 'Explică-mi conceptul', en: 'Explain the concept', fr: 'Explique le concept', de: 'Erkläre das Konzept', es: 'Explica el concepto', it: 'Spiega il concetto' };
    const examples: Record<string, string[]> = { ro: ['Care sunt ideile principale?'], en: ['What are the main ideas?'], fr: ['Quelles sont les idées principales ?'], de: ['Was sind die wichtigsten Ideen?'], es: ['¿Cuáles son las ideas principales?'], it: ['Quali sono le idee principali?'] };
    const starters = [...(examples[source.language] || examples.en), ...(source.keywords[0] ? [`${questionPrefix[source.language] || questionPrefix.en} ${source.keywords[0]}`] : [])];
    return <div className="chat-layout"><section className="chat-panel"><div className="chat-intro"><h2>O întrebare bună schimbă perspectiva.</h2><p>Răspunsurile folosesc materialul încărcat și indică fragmentele relevante. Dacă sursa nu conține răspunsul, îți spunem.</p></div><div className="chat-history" role="log" aria-live="polite" aria-label="Conversația cu materialul">{!history.length && <div><span className="eyebrow">ÎNCEARCĂ O ÎNTREBARE</span><div className="keyword-list" style={{ marginTop: 15 }}>{starters.map(text => <button key={text} onClick={() => setMessage(text)}>{text}</button>)}</div><p className="small muted" style={{ marginTop: 18 }}>Conversația rămâne în această sesiune. Răspunsul și explicațiile folosesc limba documentului: {source.language.toUpperCase()}.</p></div>}{history.map((item, index) => <div className="stack" key={index}><div className="chat-message user"><span>ÎNTREBAREA TA</span>{item.question}</div><div className="chat-message" lang={source.language}><span>{item.response.mode === 'extractive' ? 'FRAGMENTE DIN SURSĂ' : item.response.mode === 'ai_grounded' ? 'FRAGMENTE SELECTATE CU AI' : 'RĂSPUNS INDISPONIBIL ÎN SURSĂ'}</span>{item.response.answer}<Citations citations={item.response.citations} onPage={onPage}/></div></div>)}{busy && <Loading text="Căutăm în materialul tău…"/>}<div ref={bottomRef}/></div>{error && <ErrorNotice message={error}/>}<form className="chat-form" onSubmit={send}><label className="sr-only" htmlFor="chat-message">Întrebarea despre material</label><textarea id="chat-message" value={message} onChange={e => setMessage(e.target.value)} maxLength={2000} rows={2} placeholder="Ce ai vrea să înțelegi din acest material?" disabled={!user || busy} required/><button className="button primary" disabled={!user || busy || !message.trim()} aria-label="Trimite întrebarea"><Send size={18}/></button></form>{!user && <p className="small muted" style={{ padding: '0 20px 18px' }}><Link href="/account" className="text-button">Intră în cont pentru a pune întrebări.</Link></p>}</section><aside className="panel"><h2 style={{ fontSize: 26, marginBottom: 20 }}>Mai departe, cu sens.</h2><SuggestionsPanel suggestions={suggestions} onAsk={term => setMessage(`${questionPrefix[source.language] || questionPrefix.en} ${term}`)}/><p className="source-legend">Legăturile externe deschid o căutare. Verifică autorul și relevanța sursei găsite.</p></aside></div>;
}
