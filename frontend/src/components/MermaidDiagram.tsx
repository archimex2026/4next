'use client';
import { useEffect, useRef, useState } from 'react';
import { ErrorNotice } from './UI';
export default function MermaidDiagram({ chart }: {
    chart: string;
}) {
    const container = useRef<HTMLDivElement>(null);
    const [error, setError] = useState('');
    useEffect(() => { let active = true; async function draw() { try {
        const mermaid = (await import('mermaid')).default;
        mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'neutral', fontFamily: 'Arial' });
        const { svg } = await mermaid.render(`diagram-${crypto.randomUUID()}`, chart);
        if (active && container.current)
            container.current.innerHTML = svg;
    }
    catch {
        if (active)
            setError('Schema nu poate fi afișată. Folosește explicația din lecție.');
    } } void draw(); return () => { active = false; }; }, [chart]);
    return error ? <ErrorNotice message={error}/> : <div className="diagram-container" ref={container} role="img" aria-label="Schema conceptelor lecției"/>;
}
