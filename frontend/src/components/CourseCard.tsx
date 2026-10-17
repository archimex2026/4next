import Link from 'next/link';
import { ArrowUpRight, BookOpen, Clock, LockKeyhole, Globe2, Star } from 'lucide-react';
import { Course } from '@/lib/types';
export default function CourseCard({ course, index = 0 }: {
    course: Course;
    index?: number;
}) {
    const progress = Math.min(100, Math.max(0, course.completion_percentage || 0));
    return <Link href={`/courses/${course.id}`} className={`course-card tone-${index % 4}`}><div className="course-cover"><span className="eyebrow">{course.language?.toUpperCase() || 'MATERIAL'} / CAIET DE STUDIU</span><BookOpen size={34} strokeWidth={1.1}/><h3>{course.book_title || course.book?.title || course.title}</h3><span className="cover-arrow"><ArrowUpRight size={20}/></span></div><div className="course-copy"><div className="row spaced"><span className="muted small">{course.author || course.book?.author || 'Material de studiu'}</span><span className="small inline">{course.visibility === 'public' ? <Globe2 size={13}/> : <LockKeyhole size={13}/>} {course.visibility === 'public' ? 'Public' : 'Privat'}</span></div><p className="course-description">{course.overview}</p><div className="course-meta"><span><BookOpen size={14}/>{course.lesson_count || 0} lecții</span><span><Clock size={14}/>{course.estimated_duration || 'Ritmul tău'}</span></div>{course.visibility === 'public' ? <div className="course-bottom"><Star size={14}/>{(course.rating_average || 0).toFixed(1)} <span className="muted">({course.rating_count || 0} voturi)</span></div> : <><div className="course-bottom spaced"><span>{progress}% parcurs</span><span>Deschide <ArrowUpRight size={13}/></span></div><div className="progress-track"><span style={{ width: `${progress}%` }}/></div></>}</div></Link>;
}
