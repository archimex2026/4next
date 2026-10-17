import Link from 'next/link';
import { ArrowUpRight, BookOpen, Clock } from 'lucide-react';
import { Course } from '@/lib/types';

export default function CourseCard({ course, index = 0 }: { course: Course; index?: number }) {
  const progress = Math.min(100, Math.max(0, course.completion_percentage || 0));
  const author = course.author || course.book?.author;
  const authorLabel = author && !['Recognized Author', 'Autor Cunoscut', 'Autor Necunoscut', 'Unknown Author', 'Author'].includes(author) ? author : 'Materialul tău';
  return (
    <Link href={`/courses/${course.id}`} className={`study-course tone-${index % 4}`}>
      <div className="course-cover" aria-hidden="true">
        <span className="cover-label">CAIET DE STUDIU / {String(index + 1).padStart(2, '0')}</span>
        <div className="cover-art"><span /><span /><span /></div>
        <BookOpen size={27} strokeWidth={1.3} />
        <span className="course-open"><ArrowUpRight size={21} /></span>
      </div>
      <div className="course-copy">
        <span className="course-author">{authorLabel}</span>
        <h3>{course.book_title || course.book?.title || course.title}</h3>
        <div className="course-meta"><span><BookOpen size={14} />{course.lesson_count} lecții</span><span><Clock size={14} />{course.estimated_duration?.replace(/\bmins?\b/g, 'min')}</span></div>
        <div className="course-progress"><span>{progress > 0 ? `${progress}% parcurs` : 'Gata de explorat'}</span><span>{progress === 100 ? 'Finalizat' : progress > 0 ? 'Continuă' : 'Deschide'} <ArrowUpRight size={13} /></span></div>
        <div className="progress-track"><div style={{ width: `${progress}%` }} /></div>
      </div>
    </Link>
  );
}
