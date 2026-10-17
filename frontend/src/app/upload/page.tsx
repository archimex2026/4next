'use client';

import { useEffect, useState, Suspense, FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { AlignLeft, ArrowRight, BookOpen, FileText, LoaderCircle, Upload } from 'lucide-react';
import { uploadBook, fetchBook } from '@/lib/api';

function UploadContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const existingBookId = searchParams.get('book_id');
  const [mode, setMode] = useState<'file' | 'text'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [language, setLanguage] = useState<'ro' | 'en'>('ro');
  const [bookId, setBookId] = useState<string | null>(existingBookId);
  const [processing, setProcessing] = useState(!!existingBookId);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!bookId) return;
    let cancelled = false;
    const checkStatus = async () => {
      try {
        const book = await fetchBook(bookId);
        if (cancelled) return;
        if (book.status === 'ready' && book.course_id) router.push(`/courses/${book.course_id}`);
        else if (book.status === 'failed') {
          setError('Materialul nu a putut fi procesat. Încearcă un alt fișier sau lipește textul.');
          setProcessing(false);
          setBookId(null);
        }
      } catch {
        if (!cancelled) {
          setError('Nu putem verifica materialul acum. Încearcă din nou.');
          setProcessing(false);
          setBookId(null);
        }
      }
    };
    checkStatus();
    const timer = setInterval(checkStatus, 1200);
    return () => { cancelled = true; clearInterval(timer); };
  }, [bookId, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (mode === 'file' && !file) { setError('Alege un fișier pentru a începe.'); return; }
    if (mode === 'text' && text.trim().length < 50) { setError('Adaugă cel puțin 50 de caractere, ca să avem suficient context.'); return; }
    if (mode === 'file' && file && !/\.(pdf|epub|docx|doc|txt|md)$/i.test(file.name)) { setError('Alege un fișier PDF, EPUB, DOCX, DOC, TXT sau MD.'); return; }
    setError(null);
    setProcessing(true);
    try {
      const result = await uploadBook({ file: mode === 'file' ? file || undefined : undefined, text: mode === 'text' ? text : undefined, title: title.trim() || undefined, author: author.trim() || undefined, language });
      if (result.course_id) router.push(`/courses/${result.course_id}`);
      else setBookId(result.book_id);
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message : 'Materialul nu a putut fi încărcat. Încearcă din nou.');
      setProcessing(false);
    }
  }

  return (
    <div className="study-shell upload-page">
      <div className="upload-heading"><span className="eyebrow">ÎNCEPE CU CE AI DEJA</span><h1>Din material, în înțelegere.</h1><p>Adaugă un curs, o carte sau notițele tale. Le organizăm în lecții, flashcarduri și întrebări, ca să ai de unde începe.</p></div>
      <div className="upload-layout">
        {processing ? <div className="upload-status" role="status"><LoaderCircle size={32} className="animate-spin" /><h2>Pregătim spațiu pentru ideile tale.</h2><p>Organizăm materialul în lecții. Vei ajunge direct la curs când este pregătit; fișierele audio și video se pot genera în continuare.</p></div> :
          <form onSubmit={handleSubmit} className="upload-form">
            <div className="input-tabs" role="group" aria-label="Cum adaugi materialul"><button type="button" aria-pressed={mode === 'file'} onClick={() => { setMode('file'); setError(null); }}><FileText size={16} />Încarcă un fișier</button><button type="button" aria-pressed={mode === 'text'} onClick={() => { setMode('text'); setError(null); }}><AlignLeft size={16} />Lipește text</button></div>
            {error && <div className="upload-error" role="alert">{error}</div>}
            {mode === 'file' ? <label className={`file-drop ${dragging ? 'dragging' : ''}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); setFile(event.dataTransfer.files[0] || null); setError(null); }}><Upload size={30} strokeWidth={1.4} /><strong>{file ? file.name : 'Trage materialul aici sau alege un fișier'}</strong><span>{file ? `${(file.size / 1024 / 1024).toFixed(1)} MB · Poți alege alt fișier` : 'PDF, EPUB, DOCX, DOC, TXT sau MD'}</span><input type="file" aria-label="Alege materialul de studiu" accept=".pdf,.epub,.docx,.doc,.txt,.md" onChange={event => { setFile(event.target.files?.[0] || null); setError(null); }} /></label> : <label className="form-field" htmlFor="material-text">Textul tău<textarea id="material-text" value={text} onChange={event => setText(event.target.value)} placeholder="Lipește aici un capitol, notițele de la curs sau un articol…" required minLength={50} /><small>Cel puțin 50 de caractere. Cu mai mult context, ideile se leagă mai bine.</small></label>}
            <div className="form-row"><label className="form-field" htmlFor="material-title">Cum se numește materialul? <small>Opțional</small><input id="material-title" value={title} onChange={event => setTitle(event.target.value)} placeholder="De exemplu: Biologie — capitolul 3" /></label><label className="form-field" htmlFor="material-author">Autor sau sursă <small>Opțional</small><input id="material-author" value={author} onChange={event => setAuthor(event.target.value)} placeholder="De exemplu: notițe de la curs" /></label></div>
            <fieldset className="audio-language"><legend>Limba explicațiilor audio</legend><label><input type="radio" name="language" checked={language === 'ro'} onChange={() => setLanguage('ro')} />Română</label><label><input type="radio" name="language" checked={language === 'en'} onChange={() => setLanguage('en')} />Engleză</label></fieldset>
            <button type="submit" className="study-button primary form-submit">Pregătește materialul de studiu <ArrowRight size={17} /></button>
          </form>}
        <aside className="upload-aside"><span className="eyebrow">MAI MULTE FELURI DE A ÎNȚELEGE</span><h2>Un material. Multe perspective.</h2><ol><li><h3>Găsește firul ideilor</h3><p>Parcurge explicațiile și schemele, lecție cu lecție.</p></li><li><h3>Pune-ți memoria la treabă</h3><p>Revino la concepte prin flashcarduri și verifică-te cu un quiz.</p></li><li><h3>Ia învățarea cu tine</h3><p>Ascultă lecțiile audio sau descarcă ghidul de studiu.</p></li></ol><div className="aside-note"><BookOpen size={23} strokeWidth={1.4} /><p>Poți începe cu un singur capitol. Uneori, un pas mic e tot ce îți trebuie.</p></div></aside>
      </div>
    </div>
  );
}

export default function UploadPage() {
  return <Suspense fallback={<div className="study-shell upload-page"><div className="course-skeleton animate-pulse" aria-label="Se încarcă formularul" /></div>}><UploadContent /></Suspense>;
}

