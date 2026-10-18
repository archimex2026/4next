'use client';
import { useEffect, useRef, useState } from 'react';
import type { GenerationProgress as Progress } from '@/lib/types';
import { errorMessage, mutate } from '@/lib/api';
import { ErrorNotice } from './UI';

export default function GenerationProgress({ courseId, progress, isOwner, onProgress, onPage }: {
    courseId: string;
    progress: Progress;
    isOwner: boolean;
    onProgress: () => Promise<void>;
    onPage: (page: number) => void;
}) {
    const stop = useRef(false);
    const [running, setRunning] = useState(false);
    const [stopping, setStopping] = useState(false);
    const [error, setError] = useState('');
    useEffect(() => () => { stop.current = true; }, []);
    async function resume() {
        stop.current = false;
        setRunning(true);
        setStopping(false);
        setError('');
        let current = progress;
        try {
            while (current.next_index !== null && !stop.current) {
                current = await mutate<Progress>(`/api/study/${courseId}/generate-next`, { segment_index: current.next_index });
                await onProgress();
            }
        } catch (e) {
            setError(errorMessage(e));
            // A response can be lost after the server committed a segment.
            await onProgress();
        } finally {
            setRunning(false);
            setStopping(false);
        }
    }
    return <section className="panel generation-progress" aria-label="Procesarea documentului">
        <h2>Documentul, parte cu parte</h2>
        <p role="status" aria-live="polite">{progress.completed} din {progress.total} segmente salvate · {progress.processed_pages.length} pagini / secțiuni procesate · {progress.cited_pages.length} cu citări în lecții.</p>
        <progress value={progress.completed} max={progress.total} aria-label="Segmente salvate" />
        <p className="small muted">Procesarea unei pagini nu garantează că fiecare idee este explicată. Citările arată ce pagini susțin lecțiile. Verifică sursa; unele părți pot conține doar extrase.</p>
        <details><summary>Vezi planul și paginile fiecărei părți</summary><ol>
            {progress.segments.map(part => <li key={part.index}>
                <button className="text-button" type="button" onClick={() => onPage(part.pages[0])}>Pagini / secțiuni {part.pages[0]}–{part.pages.at(-1)}</button>
                {' · '}{part.status === 'pending' ? 'De procesat' : `${part.lesson_count} lecții · ${part.generation_mode === 'ai_grounded' ? 'explicații AI cu surse' : 'extrase din sursă'}`}
            </li>)}
        </ol></details>
        {error && <ErrorNotice message={error} />}
        {isOwner && progress.next_index !== null && <div className="row wrap">
            <button className="button primary" onClick={resume} disabled={running}>{running ? stopping ? 'Încheiem partea curentă…' : 'Procesăm următoarea parte…' : 'Continuă procesarea documentului'}</button>
            {running && <button className="button secondary" disabled={stopping} onClick={() => { stop.current = true; setStopping(true); }}>Oprește după partea curentă</button>}
        </div>}
        <p className="small muted">{progress.next_index !== null ? 'Părțile salvate rămân disponibile. Poți închide pagina și relua ulterior; cererea curentă poate continua pe server.' : 'Planul de procesare s-a încheiat. Acoperirea pedagogică se verifică în lecții și în sursă.'} Datele demo rămân temporare pe Render Free.</p>
    </section>;
}
