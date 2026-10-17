'use client';
import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { errorMessage, mutate } from '@/lib/api';
import { ErrorNotice } from './UI';

export default function TrashCourseButton({ courseId, title, onDeleted }: {
    courseId: string;
    title: string;
    onDeleted: () => void;
}) {
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    async function remove() {
        if (!window.confirm(`Muți „${title}” în coș?\n\nMaterialul nu va mai fi accesibil în bibliotecă sau în clase. Îl poți restaura timp de 5 zile.`)) return;
        setBusy(true);
        setError('');
        try {
            await mutate(`/api/courses/${encodeURIComponent(courseId)}`, undefined, 'DELETE');
            onDeleted();
        } catch (e) {
            setError(errorMessage(e));
        } finally {
            setBusy(false);
        }
    }
    return <div className="trash-action">{error && <ErrorNotice message={error}/>}<button className="text-button danger-text" onClick={remove} disabled={busy} aria-label={`Mută în coș: ${title}`}><Trash2 size={15}/>{busy ? 'Se mută în coș…' : 'Mută în coș'}</button></div>;
}
