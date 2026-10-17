import StudyWorkspace from '@/components/StudyWorkspace';
export default async function QuizPage({ params }: {
    params: Promise<{
        id: string;
    }>;
}) { const { id } = await params; return <StudyWorkspace courseId={id} initialTab="quiz"/>; }
