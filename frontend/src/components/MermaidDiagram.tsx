'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Copy, Check, Maximize2, Minimize2, GitGraph } from 'lucide-react';

interface MermaidDiagramProps {
  chart: string;
  title?: string;
}

export default function MermaidDiagram({ chart, title = 'Conceptual Architecture' }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function renderMermaid() {
      if (!chart) return;
      try {
        const mermaidModule = await import('mermaid');
        const mermaid = mermaidModule.default;
        mermaid.initialize({
          startOnLoad: false,
          theme: 'neutral',
          securityLevel: 'loose',
          fontFamily: 'Inter, system-ui, sans-serif',
          themeVariables: {
            primaryColor: '#315D50',
            primaryTextColor: '#FFFFFF',
            primaryBorderColor: '#315D50',
            lineColor: '#5D8271',
            secondaryColor: '#EBF3FA',
            tertiaryColor: '#F8FAFC',
          },
        });

        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);
        if (isMounted) {
          setSvgContent(svg);
          setHasError(false);
        }
      } catch (err) {
        console.warn('Mermaid rendering notice:', err);
        if (isMounted) setHasError(true);
      }
    }

    renderMermaid();

    return () => {
      isMounted = false;
    };
  }, [chart]);

  const copyCode = () => {
    navigator.clipboard.writeText(chart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadSvg = () => {
    if (!svgContent) return;
    const blob = new Blob([svgContent], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}_diagram.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadMmd = () => {
    const blob = new Blob([chart], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}_diagram.mmd`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs transition-all ${isExpanded ? 'fixed inset-6 z-50 p-6 flex flex-col bg-white shadow-2xl' : 'my-4'}`}>
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <GitGraph className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">{title}</span>
          <span className="text-[10px] font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">UML Mermaid</span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={copyCode}
            className="flex items-center gap-1 px-2.5 py-1 text-xs text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
            title="Copiază codul Mermaid"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="text-[11px] font-medium">{copied ? 'Copiat' : 'Copiază'}</span>
          </button>

          {svgContent && (
            <button
              onClick={downloadSvg}
              className="flex items-center gap-1 px-2.5 py-1 text-xs text-slate-600 hover:text-blue-600 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors font-medium"
              title="Descarcă diagramă ca fișier SVG vectorial"
            >
              <span>SVG</span>
            </button>
          )}

          <button
            onClick={downloadMmd}
            className="flex items-center gap-1 px-2.5 py-1 text-xs text-slate-600 hover:text-blue-600 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors font-medium"
            title="Descarcă codul sursă .mmd"
          >
            <span>.MMD</span>
          </button>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
            title={isExpanded ? 'Închide ecran complet' : 'Mărește diagrama'}
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Diagram Body */}
      <div
        ref={containerRef}
        className={`p-6 flex items-center justify-center overflow-auto bg-slate-50/40 ${isExpanded ? 'flex-1' : 'min-h-[200px]'}`}
      >
        {hasError ? (
          <div className="text-center py-6 text-slate-500">
            <p className="text-xs font-semibold text-slate-700">Visual Diagram Schema</p>
            <pre className="mt-2 text-xs font-mono bg-slate-100 p-3 rounded-lg text-slate-700 max-w-md mx-auto overflow-x-auto text-left">
              {chart}
            </pre>
          </div>
        ) : svgContent ? (
          <div
            className="w-full flex justify-center [&>svg]:max-w-full [&>svg]:h-auto"
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        ) : (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <div className="w-3.5 h-3.5 border-2 border-[#315D50] border-t-transparent rounded-full animate-spin" />
            <span>Rendering diagram...</span>
          </div>
        )}
      </div>
    </div>
  );
}
