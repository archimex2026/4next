import Link from 'next/link';
import { ArrowRight, BookOpen, CircleAlert, LoaderCircle } from 'lucide-react';
export function Loading({ text = 'Se încarcă materialele…' }: {
    text?: string;
}) { return <div className="loading-state" role="status"><LoaderCircle size={22}/>{text}</div>; }
export function ErrorNotice({ message, retry }: {
    message: string;
    retry?: () => void;
}) { return <div className="notice error" role="alert"><CircleAlert size={19}/><span>{message}</span>{retry && <button onClick={retry} className="text-button">Reîncearcă</button>}</div>; }
export function Empty({ title, text, href, action }: {
    title: string;
    text: string;
    href?: string;
    action?: string;
}) { return <div className="empty-state"><BookOpen size={30} strokeWidth={1.4}/><h2>{title}</h2><p>{text}</p>{href && <Link className="button primary" href={href}>{action || 'Adaugă un material'}<ArrowRight size={16}/></Link>}</div>; }
export function LoginRequired({ text = 'Intră în cont pentru a păstra materialele și progresul tău.' }: {
    text?: string;
}) { return <Empty title="Un loc al tău pentru învățat." text={text} href="/account" action="Intră în cont"/>; }
export function PageHeading({ eyebrow, title, text, children }: {
    eyebrow: string;
    title: string;
    text?: string;
    children?: React.ReactNode;
}) { return <div className="page-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1>{text && <p>{text}</p>}</div>{children}</div>; }
