'use client';
import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Copy, Plus, Trash2, UsersRound } from 'lucide-react';
import { Course, StudyGroup } from '@/lib/types';
import { errorMessage, fetchCourses, mutate, request } from '@/lib/api';
import { useAuth } from './AuthProvider';
import { Empty, ErrorNotice, Loading, LoginRequired, PageHeading } from './UI';
import CourseCard from './CourseCard';
export default function GroupWorkspace({ id }: {
    id: string;
}) {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [group, setGroup] = useState<StudyGroup | null>(null);
    const [mine, setMine] = useState<Course[]>([]);
    const [pending, setPending] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');
    const load = useCallback(() => Promise.all([request<StudyGroup>(`/api/groups/${id}`), fetchCourses('mine')]).then(([data, courses]) => { setGroup(data); setMine(courses); setError(''); }).catch(e => setError(errorMessage(e))).finally(() => setPending(false)), [id]);
    useEffect(() => { if (user)
        void load(); }, [user, load]);
    async function share(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const data = new FormData(event.currentTarget); setBusy(true); try {
        await mutate(`/api/groups/${id}/materials`, { course_id: data.get('course_id') });
        await load();
        setNotice('Materialul este disponibil membrilor clasei. Vizibilitatea în biblioteca publică nu s-a schimbat.');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function revoke(courseId: string) { setBusy(true); try {
        await mutate(`/api/groups/${id}/materials/${courseId}`, undefined, 'DELETE');
        await load();
        setNotice('Accesul clasei la acest material a fost retras.');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function remove(memberId: string) { setBusy(true); try {
        await mutate(`/api/groups/${id}/members/${memberId}`, undefined, 'DELETE');
        if (memberId === user?.id) {
            router.push('/groups');
            return;
        }
        await load();
        setNotice('Membrul a fost eliminat din clasă.');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function copy() { try {
        await navigator.clipboard.writeText(group?.invite_code || '');
        setNotice('Codul de invitație a fost copiat.');
    }
    catch {
        setNotice('Selectează și copiază codul afișat.');
    } }
    if (loading)
        return <div className="page-shell"><Loading /></div>;
    if (!user)
        return <div className="page-shell"><LoginRequired /></div>;
    if (pending)
        return <div className="page-shell"><Loading text="Se deschide clasa…"/></div>;
    if (!group)
        return <div className="page-shell"><ErrorNotice message={error || 'Clasa nu este disponibilă.'} retry={load}/></div>;
    const isOwner = group.owner_id === user.id;
    const available = mine.filter(course => !group.courses?.some(shared => shared.id === course.id));
    return <div className="page-shell"><Link href="/groups" className="back-link"><ArrowLeft size={15}/>Toate clasele</Link><PageHeading eyebrow="CLASA TA" title={group.name} text={group.subject || 'Un loc comun pentru ce aveți de învățat.'}/>{error && <ErrorNotice message={error}/>} {notice && <p className="notice" role="status">{notice}</p>}<div className="group-detail-grid"><div><section className="panel" style={{ marginBottom: 28 }}><h2>Adaugă o sursă la masă.</h2><p className="small muted" style={{ marginBottom: 20 }}>Membrii vor putea studia materialul, inclusiv dacă este privat. Își vor păstra propriile notițe, evidențieri și rezultate.</p>{available.length ? <form className="form-stack" onSubmit={share}><label>Din biblioteca ta<select name="course_id" required defaultValue=""><option value="" disabled>Alege un material</option>{available.map(course => <option key={course.id} value={course.id}>{course.book_title || course.title} ({course.visibility === 'public' ? 'public' : 'privat'})</option>)}</select></label><button className="button primary" disabled={busy}><Plus size={16}/>Oferă acces clasei</button></form> : <Link className="text-button" href="/upload">Adaugă un material în biblioteca ta <Plus size={15}/></Link>}</section><div className="section-heading" style={{ marginTop: 0 }}><div><span className="eyebrow">SURSE COMUNE</span><h2>Materialele clasei.</h2></div></div>{group.courses?.length ? <div className="course-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(min(100%,240px),1fr))' }}>{group.courses.map((course, index) => <div key={course.id}><CourseCard course={course} index={index}/>{(isOwner || course.shared_by === user.id) && <button className="text-button" disabled={busy} onClick={() => revoke(course.id)}><Trash2 size={14}/>Retrage din clasă</button>}</div>)}</div> : <Empty title="Aici adunăm sursele." text="Alege un material de mai sus pentru a începe studiul împreună."/>}</div><aside className="stack"><section className="panel"><UsersRound size={24} strokeWidth={1.3}/><h2 style={{ marginTop: 15, fontSize: 27 }}>Invită un coleg.</h2><p className="small muted" style={{ marginTop: 13 }}>Oricine are codul se poate alătura clasei. Trimite-l doar celor cu care vrei să studiezi.</p><div className="invite-code">{group.invite_code}</div><button className="button secondary" onClick={copy}><Copy size={15}/>Copiază codul</button></section><section className="panel"><h2 style={{ fontSize: 26 }}>Oameni, nu doar idei.</h2><ul className="member-list">{group.members?.map(member => <li key={member.id}><div className="row spaced"><span>{member.name}{member.id === group.owner_id && <small className="muted"> · administrator</small>}</span>{isOwner && member.id !== user.id && <button className="icon-button" disabled={busy} aria-label={`Elimină ${member.name} din clasă`} onClick={() => remove(member.id)}><Trash2 size={14}/></button>}</div></li>)}</ul>{!isOwner && <button className="text-button" disabled={busy} onClick={() => remove(user.id)}>Părăsește clasa <ArrowLeft size={14}/></button>}</section></aside></div></div>;
}
