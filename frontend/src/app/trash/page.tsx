'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, RotateCcw, Trash2 } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';
import { Empty, ErrorNotice, Loading, LoginRequired, PageHeading } from '@/components/UI';
import { errorMessage, mutate, request } from '@/lib/api';
import { TrashedCourse } from '@/lib/types';

export default function TrashPage() {
    const { user, loading, error } = useAuth();
    return <div className="page-shell"><PageHeading eyebrow="BIBLIOTECA TA" title="Coșul de gunoi" text="Ai timp să te răzgândești. Materialele rămân aici 5 zile de la ștergere, apoi sunt eliminate definitiv."><Link href="/dashboard" className="button secondary"><ArrowLeft size={16}/>Biblioteca mea</Link></PageHeading>{loading ? <Loading text="Se verifică sesiunea…"/> : error ? <ErrorNotice message={error}/> : user ? <TrashList key={user.id}/> : <LoginRequired text="Intră în cont pentru a vedea și restaura materialele tale șterse."/>}</div>;
}

function formatDate(timestamp: string) {
    return new Intl.DateTimeFormat('ro-RO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(timestamp));
}

function TrashList() {
    const [items, setItems] = useState<TrashedCourse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');
    const [busy, setBusy] = useState('');
    const noticeRef = useRef<HTMLParagraphElement>(null);
    const load = useCallback(() => request<{ items: TrashedCourse[]; retention_days: number }>('/api/trash')
        .then(data => { setItems(data.items); setError(''); })
        .catch(e => setError(errorMessage(e)))
        .finally(() => setLoading(false)), []);
    useEffect(() => { void load(); }, [load]);
    useEffect(() => { if (notice) noticeRef.current?.focus(); }, [notice]);
    async function act(item: TrashedCourse, restore: boolean) {
        if (!restore && !window.confirm(`Ștergi definitiv „${item.title}”?\n\nDocumentul, materialele generate și datele de studiu asociate vor fi eliminate. Această acțiune nu poate fi anulată.`)) return;
        setBusy(item.id);
        setError('');
        setNotice('');
        try {
            await mutate(`/api/trash/${encodeURIComponent(item.id)}${restore ? '/restore' : ''}`, undefined, restore ? 'POST' : 'DELETE');
            setItems(current => current.filter(entry => entry.id !== item.id));
            setNotice(restore ? `„${item.title}” a fost restaurat ca material privat în biblioteca ta. Îl poți publica sau partaja din nou.` : `„${item.title}” a fost șters definitiv.`);
        } catch (e) {
            setError(errorMessage(e));
        } finally {
            setBusy('');
        }
    }
    if (loading) return <Loading text="Se deschide coșul de gunoi…"/>;
    return <>{error && <ErrorNotice message={error} retry={load}/>} {notice && <p className="notice success" role="status" ref={noticeRef} tabIndex={-1}>{notice}</p>}{items.length ? <><p className="small muted trash-help">Doar tu vezi aceste materiale. Restaurarea le păstrează private; publicarea și partajarea în clase se fac din nou, la alegerea ta. Datele de mai jos sunt afișate în fusul orar al dispozitivului.</p><div className="trash-list">{items.map(item => <article key={item.id} className="trash-item"><div className="trash-item-copy"><span className="eyebrow">{item.language?.toUpperCase() || 'MATERIAL'} / ÎN COȘ</span><h2>{item.title}</h2>{item.description && <p className="trash-description">{item.description}</p>}<dl className="trash-dates"><div><dt>Mutat în coș</dt><dd><time dateTime={item.deleted_at}>{formatDate(item.deleted_at)}</time></dd></div><div><dt>Ștergere definitivă</dt><dd><time dateTime={item.purge_at}>{formatDate(item.purge_at)}</time></dd></div></dl></div><div className="trash-item-actions"><button className="button secondary" onClick={() => act(item, true)} disabled={!!busy} aria-label={`Restaurează: ${item.title}`}><RotateCcw size={16}/>{busy === item.id ? 'Se procesează…' : 'Restaurează'}</button><button className="text-button danger-text" onClick={() => act(item, false)} disabled={!!busy} aria-label={`Șterge definitiv: ${item.title}`}><Trash2 size={15}/>Șterge definitiv</button></div></article>)}</div></> : !error && <Empty title="Totul este la locul lui." text="Nu ai materiale în coș. Când ștergi un material din biblioteca ta, îl poți recupera de aici timp de 5 zile." href="/dashboard" action="Înapoi la bibliotecă"/>}</>;
}
