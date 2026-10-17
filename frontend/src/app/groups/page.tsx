'use client';
import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowUpRight, Plus, UsersRound } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';
import { Empty, ErrorNotice, Loading, LoginRequired, PageHeading } from '@/components/UI';
import { errorMessage, mutate, request } from '@/lib/api';
import { StudyGroup } from '@/lib/types';
export default function Groups() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [groups, setGroups] = useState<StudyGroup[]>([]);
    const [pending, setPending] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const load = useCallback(() => request<StudyGroup[]>('/api/groups').then(data => { setGroups(data); setError(''); }).catch(e => setError(errorMessage(e))).finally(() => setPending(false)), []);
    useEffect(() => { if (user)
        void load(); }, [user, load]);
    async function submit(event: FormEvent<HTMLFormElement>, join = false) { event.preventDefault(); const form = new FormData(event.currentTarget); setBusy(true); setError(''); try {
        const group = await mutate<StudyGroup>(join ? '/api/groups/join' : '/api/groups', join ? { code: form.get('code') } : { name: form.get('name'), subject: form.get('subject') });
        router.push(`/groups/${group.id}`);
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
        return <div className="page-shell"><LoginRequired text="Creează o clasă, invită colegi și studiați aceleași surse, fiecare cu notițele și progresul său."/></div>;
    return <div className="page-shell"><PageHeading eyebrow="ÎNVĂȚĂM ÎMPREUNĂ" title="O masă mai mare pentru idei." text="Adună oamenii și materialele în jurul unui subiect. Notițele și progresul rămân personale."/>{error && <ErrorNotice message={error}/>}<div className="groups-grid"><section className="panel"><h2>Creează o clasă.</h2><form className="form-stack" onSubmit={event => submit(event)}><label>Numele clasei<input name="name" required maxLength={100} placeholder="ex. Biologie pentru Bac"/></label><label>Subiectul de studiu<input name="subject" maxLength={160} placeholder="ex. Anatomie și fiziologie"/></label><button className="button primary" disabled={busy}><Plus size={16}/>Creează clasa</button></form></section><section className="panel" style={{ background: 'var(--sage)' }}><h2>Ai primit o invitație?</h2><p className="muted small" style={{ marginBottom: 24 }}>Cere codul unui coleg care este deja în clasă.</p><form className="form-stack" onSubmit={event => submit(event, true)}><label>Codul de invitație<input name="code" required minLength={6} maxLength={32} placeholder="Introdu codul clasei" autoCapitalize="characters" autoComplete="off"/></label><button className="button secondary" disabled={busy}><UsersRound size={16}/>Intră în clasă</button></form></section></div><div className="section-heading"><div><span className="eyebrow">CLASELE TALE</span><h2>Cu cine înveți?</h2></div></div>{pending ? <Loading /> : groups.length ? <div className="group-list">{groups.map(group => <Link key={group.id} href={`/groups/${group.id}`} className="group-link"><div><h2>{group.name}</h2><p className="small muted">{group.subject || 'Un spațiu pentru studiu'} · {group.member_count || 1} membri · {group.material_count || 0} materiale</p></div><ArrowUpRight size={22}/></Link>)}</div> : <Empty title="Prima clasă începe cu voi." text="Creează o clasă mai sus sau folosește un cod de invitație."/>}</div>;
}
