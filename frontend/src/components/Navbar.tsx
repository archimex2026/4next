'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ArrowUpRight, Plus, UserRound, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from './AuthProvider';
export default function Navbar() {
    const pathname = usePathname();
    const { user } = useAuth();
    const [open, setOpen] = useState(false);
    const links = [['/dashboard', 'Biblioteca mea'], ['/discover', 'Explorează'], ['/groups', 'Clase'], ['/roadmap', 'Ce urmează']];
    return <header className="site-header"><div className="nav-shell"><Link href="/" className="brand" aria-label="4next — acasă"><span className="brand-mark"><ArrowUpRight size={21}/></span>4next<span className="brand-dot">.</span></Link><button className="icon-button mobile-toggle" aria-label={open ? 'Închide meniul' : 'Deschide meniul'} aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button><nav className={open ? 'nav-links is-open' : 'nav-links'} aria-label="Navigare principală">{links.map(([href, label]) => <Link key={href} href={href} aria-current={pathname === href ? 'page' : undefined} onClick={() => setOpen(false)}>{label}</Link>)}<Link href="/account" className="account-link" onClick={() => setOpen(false)}><UserRound size={17}/>{user ? user.name.split(' ')[0] : 'Contul meu'}</Link><Link href="/upload" className="button primary nav-add" onClick={() => setOpen(false)}><Plus size={17}/>Material nou</Link></nav></div></header>;
}
