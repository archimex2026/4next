import StudyWorkspace from '@/components/StudyWorkspace';
export default async function VideoPage({ params }: {
    params: Promise<{
        id: string;
        lessonId: string;
    }>;
}) { const { id, lessonId } = await params; return <StudyWorkspace courseId={id} initialLessonId={lessonId}/>; }
