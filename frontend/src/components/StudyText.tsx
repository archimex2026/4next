/** Plain React text: support fenced code without executing model HTML or scripts. */
export default function StudyText({ text }: { text: string }) {
    return <div className="lesson-text">{text.split(/(```[\s\S]*?```)/g).map((part, index) =>
        part.startsWith('```') ? <pre key={index} style={{ overflowX: 'auto', padding: 16, background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: 8, fontSize: '0.85em', lineHeight: 1.6 }}><code>{part.replace(/^```[^\n]*\n?/, '').replace(/```$/, '')}</code></pre>
            : part.trim() ? <p key={index} style={{ whiteSpace: 'pre-wrap' }}>{part}</p> : null
    )}</div>;
}
