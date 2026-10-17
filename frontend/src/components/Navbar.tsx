'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ArrowUpRight, Plus } from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();
  return (
    <header className="study-header">
      <div className="study-nav">
        <Link href="/" className="study-brand" aria-label="4next — pagina principală">
          <span className="brand-mark"><ArrowUpRight size={23} strokeWidth={2.5} /></span>
          4next<span className="brand-dot">.</span>
        </Link>
        <nav aria-label="Navigare principală" className="study-nav-links">
          <Link href="/" aria-current={pathname === '/' ? 'page' : undefined}>Spațiul meu</Link>
          <Link href="/dashboard" aria-current={pathname === '/dashboard' || pathname.startsWith('/courses') ? 'page' : undefined}>Bibliotecă</Link>
        </nav>
        <Link href="/upload" className="study-button primary nav-upload" aria-label="Adaugă un material nou"><Plus size={17} /><span>Material nou</span></Link>
      </div>
    </header>
  );
}
