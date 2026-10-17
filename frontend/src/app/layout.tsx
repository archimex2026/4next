import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';
import Link from 'next/link';

export const metadata: Metadata = {
  icons: { icon: '/study-mark.svg' },
  title: '4next — Loc pentru idei. Timp pentru învățat.',
  description: 'Materialele tale, organizate pentru studiu. Învață cu lecții, flashcarduri, quizuri și explicații audio, în ritmul tău.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ro">
      <body>
        <a href="#main-content" className="skip-link">Sari la conținut</a>
        <Navbar />
        <main id="main-content">{children}</main>
        <footer className="study-footer">
          <span><strong>4next.</strong> Un loc pentru următoarea ta idee.</span>
          <div><Link href="/dashboard">Bibliotecă</Link><Link href="/upload">Adaugă material</Link><span>Cu pași mici, mai departe.</span></div>
        </footer>
      </body>
    </html>
  );
}
