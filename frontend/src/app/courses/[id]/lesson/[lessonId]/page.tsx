import StudyWorkspace from '@/components/StudyWorkspace';
export default async function LessonPage({ params }: {
    params: Promise<{
        id: string;
        lessonId: string;
    }>;
}) { const { id, lessonId } = await params; return <StudyWorkspace courseId={id} initialLessonId={lessonId}/>; }
