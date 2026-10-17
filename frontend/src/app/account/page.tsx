'use client';
import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, LogOut, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';
import { errorMessage, mutate } from '@/lib/api';
import { ErrorNotice, Loading, PageHeading } from '@/components/UI';
import { User } from '@/lib/types';
export default function Account() {
    const { user, loading, error: connectionError, refresh } = useAuth();
    const [mode, setMode] = useState<'login' | 'register'>('login');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');
    async function authenticate(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); setBusy(true); setError(''); try {
        await mutate(`/api/auth/${mode}`, { name: form.get('name'), email: form.get('email'), password: form.get('password'), accept_terms: form.get('accept_terms') === 'on' });
        await refresh();
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function logout() { setBusy(true); try {
        await mutate('/api/auth/logout');
        await refresh();
        setNotice('Te-ai deconectat.');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function save(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const data = new FormData(event.currentTarget); setBusy(true); setError(''); try {
        await mutate<{
            user: User;
        }>('/api/auth/profile', { name: data.get('name'), study_minutes: Number(data.get('study_minutes')), depth: data.get('depth'), exam_goal: data.get('exam_goal') }, 'PATCH');
        await refresh();
        setNotice('Preferințele tale au fost salvate.');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    if (loading)
        return <div className="page-shell"><Loading text="Se verifică sesiunea…"/></div>;
    return <div className="page-shell account-page"><PageHeading eyebrow="CONTUL TĂU" title={user ? `Bine ai venit, ${user.name.split(' ')[0]}.` : 'Fă-ți loc pentru învățat.'} text={user ? 'Un obiectiv clar și un ritm care ți se potrivește.' : 'Păstrează-ți materialele, notițele și progresul în biblioteca personală.'}/><div className="account-grid"><section className="panel">{error || connectionError ? <ErrorNotice message={error || connectionError}/> : null}{notice && <p className="notice success" role="status">{notice}</p>}{user ? <><div className="row spaced"><div><h2>Preferințe de studiu</h2><p className="muted small">{user.email}</p></div><button className="text-button" onClick={logout} disabled={busy}><LogOut size={16}/>Ieși din cont</button></div><form key={user.id} onSubmit={save} className="form-stack"><label>Numele tău<input name="name" defaultValue={user.name} required maxLength={80}/></label><label>Obiectiv de examen<input name="exam_goal" defaultValue={user.exam_goal || ''} placeholder="ex. Bacalaureat — biologie" maxLength={200}/><small>Îl salvăm în profil. Nu identificăm încă automat programa.</small></label><div className="form-columns"><label>Minute / sesiune<input name="study_minutes" type="number" min={5} max={120} step={5} defaultValue={user.study_minutes || 20} required/></label><label>Profunzime<select name="depth" defaultValue={user.depth || 'standard'}><option value="brief">Esențial</option><option value="standard">Echilibrat</option><option value="deep">În profunzime</option></select></label></div><button className="button primary" disabled={busy}>{busy ? 'Se salvează…' : 'Salvează preferințele'}</button></form></> : <><div className="segmented" aria-label="Tip de autentificare"><button className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError(''); }}>Intră în cont</button><button className={mode === 'register' ? 'active' : ''} onClick={() => { setMode('register'); setError(''); }}>Creează un cont</button></div><form onSubmit={authenticate} className="form-stack">{mode === 'register' && <label>Numele tău<input name="name" autoComplete="name" required minLength={2} maxLength={80}/></label>}<label>Email<input name="email" type="email" autoComplete="email" required/></label><label>Parolă<input name="password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={mode === 'register' ? 12 : undefined} maxLength={128} required/>{mode === 'register' && <small>Cel puțin 12 caractere.</small>}</label>{mode === 'register' && <label className="checkbox-label"><input name="accept_terms" type="checkbox" required/><span>Am citit <Link href="/terms">termenii prototipului</Link> și <Link href="/privacy">nota de confidențialitate</Link>.</span></label>}<button className="button primary" disabled={busy}>{busy ? 'Se verifică…' : mode === 'login' ? 'Intră în cont' : 'Creează contul'}<ArrowRight size={17}/></button></form></>}</section><aside className="account-aside"><ShieldCheck size={28} strokeWidth={1.3}/><h2>Studiul tău,<br /><em>spațiul tău.</em></h2><p>Documentele sunt private implicit. Tu alegi când le publici sau când le împărtășești cu o clasă.</p><div className="divider"/><p className="small">4next este un prototip în dezvoltare. Folosește materiale pe care ai dreptul să le încarci și verifică explicațiile cu sursa.</p><Link href="/dashboard" className="text-button">Mergi la bibliotecă <ArrowRight size={16}/></Link></aside></div></div>;
}
