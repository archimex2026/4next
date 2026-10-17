import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';
import Link from 'next/link';
import { AuthProvider } from '@/components/AuthProvider';
export const metadata: Metadata = {
    icons: { icon: '/study-mark.svg' },
    title: '4next — Loc pentru idei. Timp pentru învățat.',
    description: 'Materialele tale, organizate pentru studiu. Învață cu lecții, flashcarduri, quizuri și explicații audio, în ritmul tău.',
};
export default function RootLayout({ children }: Readonly<{
    children: React.ReactNode;
}>) {
    return (<html lang="ro">
      <body>
        <a href="#main-content" className="skip-link">Sari la conținut</a>
        <AuthProvider><Navbar />
        {process.env.NEXT_PUBLIC_STORAGE_MODE === 'ephemeral' && <aside className="demo-storage-notice" aria-label="Datele demo-ului gratuit"><p><strong>Demo gratuit</strong> · Conturile și materialele se pot reseta la repornirea serverului. Păstrează o copie a documentelor. <Link href="/privacy">Despre datele tale</Link></p></aside>}
        <main id="main-content">{children}</main>
        <footer className="study-footer">
          <span><strong>4next.</strong> Un loc pentru următoarea ta idee.</span>
          <div><Link href="/terms">Termeni</Link><Link href="/privacy">Confidențialitate</Link><Link href="/roadmap">Ce pregătim</Link><span>Prototip în dezvoltare</span></div>
        </footer></AuthProvider>
      </body>
    </html>);
}
