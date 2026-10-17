import Library from '@/components/Library';
export default async function Discover({ searchParams }: {
    searchParams: Promise<{
        q?: string;
    }>;
}) { const { q } = await searchParams; return <div className="page-shell"><Library isPublic initialQuery={q || ''}/></div>; }
