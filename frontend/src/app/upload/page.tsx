'use client';
import { FormEvent, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileUp, Languages, LockKeyhole, ArrowRight, Search, Check } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';
import { errorMessage, request, uploadBook } from '@/lib/api';
import { ErrorNotice, Loading, LoginRequired, PageHeading } from '@/components/UI';
interface Inspection {
    title: string;
    page_count: number;
    page_kind: string;
    language: string;
    language_supported: boolean;
    language_confirmation_required: boolean;
    language_confidence: number;
    keywords: string[];
    supported_languages: Record<string, string>;
}
const uploadLimitMb = Number(process.env.NEXT_PUBLIC_UPLOAD_LIMIT_MB || (process.env.NODE_ENV === 'production' ? '4' : '15'));
export default function Upload() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const formRef = useRef<HTMLFormElement>(null);
    const sourceRevision = useRef(0);
    const [mode, setMode] = useState<'file' | 'text'>('file');
    const [file, setFile] = useState<File>();
    const [busy, setBusy] = useState(false);
    const [inspecting, setInspecting] = useState(false);
    const [error, setError] = useState('');
    const [preview, setPreview] = useState<Inspection | null>(null);
    const [selected, setSelected] = useState<string[]>([]);
    function clear() { sourceRevision.current += 1; setPreview(null); setSelected([]); setError(''); }
    async function inspect() { const form = formRef.current; if (!form)
        return; const data = new FormData(form); const source = new FormData(); if (mode === 'file') {
        if (!file) {
            setError('Alege un fișier pentru a continua.');
            return;
        }
        if (file.size > uploadLimitMb * 1024 * 1024) {
            setError(`Fișierul depășește limita de ${uploadLimitMb} MB. Alege un document mai mic sau împarte-l în capitole.`);
            return;
        }
        source.append('file', file);
    }
    else {
        const text = String(data.get('text') || '');
        if (text.trim().length < 80) {
            setError('Adaugă cel puțin 80 de caractere pentru a putea analiza materialul.');
            return;
        }
        source.append('text', text);
    } const revision = sourceRevision.current; setInspecting(true); setError(''); try {
        const result = await request<Inspection>('/api/books/inspect', { method: 'POST', body: source });
        if (revision === sourceRevision.current) { setPreview(result); setSelected([]); }
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setInspecting(false);
    } }
    async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (!preview) {
        await inspect();
        return;
    } if (!preview.language_supported && !preview.language_confirmation_required) {
        setError('Limba documentului nu este încă suportată.');
        return;
    } const data = new FormData(event.currentTarget); setBusy(true); setError(''); try {
        const result = await uploadBook({ file: mode === 'file' ? file : undefined, text: mode === 'text' ? String(data.get('text')) : undefined, title: String(data.get('title') || ''), author: String(data.get('author') || ''), visibility: String(data.get('visibility')), study_minutes: Number(data.get('study_minutes')), depth: String(data.get('depth')), focus_keywords: JSON.stringify(selected), language: preview.language_confirmation_required ? String(data.get('language') || '') : undefined });
        if (!result.course_id)
            throw new Error('Documentul a fost primit, dar cursul nu este încă disponibil. Verifică biblioteca.');
        router.push(`/courses/${result.course_id}`);
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    if (loading)
        return <div className="page-shell"><Loading /></div>;
    if (!user)
        return <div className="page-shell"><LoginRequired /></div>;
    return <div className="page-shell upload-page"><PageHeading eyebrow="UN MATERIAL NOU" title="De la pagini la idei clare." text="Adaugă sursa. Alegem conceptele, apoi ritmul în care le aprofundăm."/><form ref={formRef} className="upload-grid" onSubmit={submit}><section className="panel"><div className="step-label">01 <span>MATERIALUL TĂU</span></div><div className="segmented"><button type="button" className={mode === 'file' ? 'active' : ''} onClick={() => { setMode('file'); clear(); }}>Încarcă un fișier</button><button type="button" className={mode === 'text' ? 'active' : ''} onClick={() => { setMode('text'); clear(); }}>Adaugă text</button></div>{mode === 'file' ? <label className="file-drop"><FileUp size={35} strokeWidth={1.2}/><strong>{file ? file.name : 'Alege documentul tău'}</strong><span>{file ? `${(file.size / 1024 / 1024).toFixed(1)} MB · apasă pentru a schimba` : 'PDF, EPUB, DOCX, TXT sau MD'}</span><input aria-label="Fișier de studiu" type="file" accept=".pdf,.epub,.docx,.txt,.md" onChange={e => { setFile(e.target.files?.[0]); clear(); }}/></label> : <label className="form-stack">Textul materialului<textarea name="text" rows={9} minLength={80} required placeholder="Lipește aici notițele sau conținutul lecției…" onChange={clear}/></label>}<div className="form-stack"><label>Titlu <span className="muted">(opțional)</span><input name="title" maxLength={200} placeholder="ex. Sistemul nervos — recapitulare"/></label><label>Autor / sursă <span className="muted">(opțional)</span><input name="author" maxLength={150} placeholder="Autorul sau sursa documentului"/></label></div><p className="small muted">Fișiere de până la {uploadLimitMb} MB. Pentru materiale mari, încarcă pe rând capitolele.</p><div className="notice"><Languages size={20}/><span>Detectăm limba sursei. Lecțiile, quizurile și explicațiile rămân în aceeași limbă.</span></div><button className="button secondary" type="button" onClick={inspect} disabled={inspecting || busy}><Search size={16}/>{inspecting ? 'Analizăm sursa…' : preview ? 'Analizează din nou' : 'Analizează limba și conceptele'}</button>{preview && <section style={{ marginTop: 26 }}><div className="row spaced"><span className="eyebrow">SURSA A FOST ANALIZATĂ</span><Check size={18}/></div><p className="small muted" style={{ marginTop: 12 }}>{preview.page_count} {preview.page_kind === 'page' ? 'pagini' : 'secțiuni'} · {preview.language_supported ? `Limbă: ${preview.supported_languages[preview.language] || preview.language.toUpperCase()}` : 'Limba necesită verificare'}</p>{preview.language_confirmation_required ? <label className="form-stack" style={{ marginTop: 18 }}>Confirmă limba documentului<select name="language" required defaultValue=""><option value="" disabled>Alege limba</option>{Object.entries(preview.supported_languages).map(([code, label]) => <option key={code} value={code}>{label}</option>)}</select><small>Detectarea nu este suficient de sigură. Confirmă limba originală, fără traducere.</small></label> : !preview.language_supported ? <ErrorNotice message="Această limbă nu este încă suportată. Nu vom traduce automat materialul."/> : null}<h3 style={{ marginTop: 22, marginBottom: 9 }}>Pe ce idei ne concentrăm?</h3><p className="small muted" style={{ marginBottom: 14 }}>Alege până la 10 concepte din sursă sau lasă toate ideile incluse.</p><div className="keyword-list" lang={preview.language}>{preview.keywords.map(term => <button type="button" key={term} aria-pressed={selected.includes(term)} onClick={() => setSelected(items => items.includes(term) ? items.filter(item => item !== term) : items.length < 10 ? [...items, term] : items)} style={selected.includes(term) ? { background: 'var(--green)', color: 'white', borderColor: 'var(--green)' } : undefined}>{selected.includes(term) && '✓ '}{term}</button>)}</div><p className="source-legend">{selected.length ? `${selected.length} concepte selectate pentru aprofundare` : 'Vom folosi întregul material.'}</p></section>}</section><aside className="panel"><div className="step-label">02 <span>ÎN RITMUL TĂU</span></div><div className="form-stack"><label>Timp pentru o sesiune<select name="study_minutes" defaultValue={user.study_minutes || 20}>{[5, 10, 15, 20, 30, 45, 60, 90, 120].map(value => <option key={value} value={value}>{value} minute</option>)}</select></label><label>Cât de mult aprofundăm?<select name="depth" defaultValue={user.depth || 'standard'}><option value="brief">Esențial — ideile de bază</option><option value="standard">Echilibrat — explicații și exemple</option><option value="deep">În profunzime — mai mult context</option></select></label><label>Cine poate vedea materialul?<select name="visibility" defaultValue="private"><option value="private">Privat — doar eu și clasele alese</option><option value="public">Public — în biblioteca comunității</option></select></label><p className="small muted inline"><LockKeyhole size={17}/>Publică numai materiale pe care ai dreptul să le distribui.</p>{error && <ErrorNotice message={error}/>}<button className="button primary" disabled={busy || inspecting || !!(preview && !preview.language_supported && !preview.language_confirmation_required)}>{busy ? 'Pregătim spațiul de studiu…' : preview ? 'Creează spațiul de studiu' : 'Analizează materialul'}{!busy && <ArrowRight size={17}/>}</button><p className="small muted">{preview ? 'Ai verificat sursa. Poți crea acum materialele de studiu. Procesarea poate dura.' : 'Mai întâi analizăm sursa, apoi alegi conceptele înainte de generare.'}</p></div></aside></form></div>;
}
