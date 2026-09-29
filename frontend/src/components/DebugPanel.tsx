import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp, Copy, Check, Cpu, Layers, X, Activity, Search, HelpCircle, CheckCircle2 } from 'lucide-react';
import type { DiagnosticDebugMetadata, ClarificationTurnRecord, Context, StructuredTroubleshootResponse } from '../types/api';

interface DebugPanelProps {
  apiResponse?: StructuredTroubleshootResponse | null;
  debugInfo?: DiagnosticDebugMetadata | null;
  sessionId?: string | null;
  turnCount?: number;
  maxTurns?: number;
  clarificationHistory?: ClarificationTurnRecord[];
  activeContext?: Context | null;
  currentQuery?: string;
  isOpen: boolean;
  onToggle: () => void;
  onClose?: () => void;
}

export const DebugPanel: React.FC<DebugPanelProps> = ({
  apiResponse,
  debugInfo,
  sessionId,
  turnCount,
  maxTurns,
  clarificationHistory,
  activeContext,
  currentQuery,
  isOpen,
  onToggle,
  onClose,
}) => {
  const [showRawJson, setShowRawJson] = useState(false);
  const [copied, setCopied] = useState(false);

  // If no debugInfo or apiResponse is provided, do not render
  const effectiveDebugInfo = debugInfo || apiResponse?.debug_info;
  const effectiveSessionId = sessionId || apiResponse?.session_id;
  const effectiveTurnCount = turnCount ?? apiResponse?.turn_count ?? 1;
  const effectiveMaxTurns = maxTurns ?? apiResponse?.max_turns ?? 3;
  const effectiveHistory = clarificationHistory || apiResponse?.clarification_history || [];

  if (!effectiveDebugInfo && !apiResponse) {
    return null;
  }

  const qu = effectiveDebugInfo?.query_understanding;
  const retrieval = effectiveDebugInfo?.retrieval;
  const latency = effectiveDebugInfo?.latency;

  const originalQuery = qu?.original_query || currentQuery || '—';
  const canonicalQuery = qu?.canonical_symptom || qu?.normalized_query || originalQuery;
  const detectedDomain = qu?.domain || apiResponse?.domain || 'Unknown';
  const selectedProblem = activeContext?.title || apiResponse?.final_problem_id || apiResponse?.contexts?.[0]?.title || '—';
  const matchConfidence = apiResponse?.confidence != null
    ? `${Math.round(apiResponse.confidence * 100)}%`
    : activeContext?.score != null
    ? `${Math.round(activeContext.score * 100)}%`
    : qu?.confidence != null
    ? `${Math.round(qu.confidence * 100)}%`
    : '—';

  const handleCopyJson = () => {
    const payload = apiResponse || {
      sessionId: effectiveSessionId,
      turnCount: effectiveTurnCount,
      maxTurns: effectiveMaxTurns,
      clarificationHistory: effectiveHistory,
      debugInfo: effectiveDebugInfo,
      activeContext,
    };
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <aside className="debug-panel view-transition" role="region" aria-label="Developer Diagnostic Pipeline Inspector">
      {/* Header Bar */}
      <div className="debug-header" onClick={onToggle} style={{ cursor: 'pointer', userSelect: 'none' }}>
        <div className="debug-title">
          <Terminal size={18} color="#38bdf8" />
          <span>Diagnostic Pipeline Inspector</span>
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              background: '#0284c7',
              color: '#ffffff',
              padding: '0.15rem 0.5rem',
              borderRadius: '9999px',
              marginLeft: '0.25rem',
            }}
          >
            Developer
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#94a3b8', fontSize: '0.85rem' }}>
          <button
            type="button"
            className="debug-header-action"
            onClick={(e) => {
              e.stopPropagation();
              onToggle();
            }}
            aria-label={isOpen ? 'Collapse Pipeline Inspector' : 'Expand Pipeline Inspector'}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.82rem' }}
          >
            <span>{isOpen ? 'Collapse' : 'Inspect'}</span>
            {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {onClose && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              title="Close Developer Mode"
              aria-label="Close Developer Mode"
              style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', padding: '0.2rem' }}
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {isOpen && (
        <div className="debug-content" style={{ padding: '1.25rem', background: '#0f172a', color: '#f8fafc' }}>
          {/* Multi-Turn Session Status Bar */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '0.75rem',
              marginBottom: '1.25rem',
              padding: '0.75rem 1rem',
              background: '#1e293b',
              borderRadius: '8px',
              border: '1px solid #334155',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Layers size={14} color="#38bdf8" />
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700 }}>TURN:</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#f8fafc' }}>
                  {effectiveTurnCount} / {effectiveMaxTurns}
                </span>
              </div>

              {apiResponse?.status && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Activity size={14} color="#38bdf8" />
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700 }}>STATUS:</span>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      fontFamily: 'monospace',
                      color:
                        apiResponse.status === 'diagnosis_ready'
                          ? '#4ade80'
                          : apiResponse.status === 'clarification_required'
                          ? '#facc15'
                          : '#f87171',
                    }}
                  >
                    {apiResponse.status}
                  </span>
                </div>
              )}
            </div>

            {effectiveSessionId && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Session ID:</span>
                <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#38bdf8' }}>
                  {effectiveSessionId}
                </span>
              </div>
            )}
          </div>

          {/* Top Key Metrics Grid */}
          <div className="debug-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem', marginBottom: '1.25rem' }}>
            {/* 1. Query Understanding Domain */}
            <div className="debug-item" style={{ background: '#1e293b', padding: '0.85rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div className="debug-label" style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
                Query Understanding
              </div>
              <div className="debug-value" style={{ color: '#38bdf8', fontSize: '1.05rem', fontWeight: 800, marginTop: '0.2rem' }}>
                {detectedDomain.toUpperCase()} ({matchConfidence})
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                Rewrite: <span style={{ color: '#e2e8f0', fontFamily: 'monospace' }}>{qu?.rewrite_method || 'direct'}</span>
              </div>
            </div>

            {/* 2. Decision Gating */}
            <div className="debug-item" style={{ background: '#1e293b', padding: '0.85rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div className="debug-label" style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
                Decision Gating
              </div>
              <div
                className="debug-value"
                style={{
                  color: retrieval?.decision === 'MATCH' ? '#4ade80' : retrieval?.decision === 'CLARIFY' ? '#facc15' : '#f87171',
                  fontSize: '1.05rem',
                  fontWeight: 800,
                  marginTop: '0.2rem',
                }}
              >
                {retrieval?.decision || (apiResponse?.contexts?.length ? 'MATCH' : 'FALLBACK')} {retrieval?.confidence_level ? `(${retrieval.confidence_level})` : ''}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                Threshold: <span style={{ color: '#e2e8f0', fontFamily: 'monospace' }}>{retrieval?.similarity_threshold?.toFixed(2) ?? '0.40'}</span>
              </div>
            </div>

            {/* 3. Latency Breakdown */}
            <div className="debug-item" style={{ background: '#1e293b', padding: '0.85rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div className="debug-label" style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
                Total Pipeline Latency
              </div>
              <div className="debug-value" style={{ color: '#facc15', fontSize: '1.05rem', fontWeight: 800, marginTop: '0.2rem' }}>
                {latency ? `${latency.total_pipeline_ms.toFixed(1)} ms` : '—'}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                QU: {latency?.query_understanding_ms.toFixed(1) ?? '—'}ms • Ret: {latency?.retrieval_ms.toFixed(1) ?? '—'}ms • Syn: {latency?.response_synthesis_ms.toFixed(1) ?? '—'}ms
              </div>
            </div>
          </div>

          {/* Section: Query & Canonical Transformation */}
          <div style={{ marginBottom: '1.25rem', background: '#1e293b', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', color: '#38bdf8', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <Search size={14} />
              <span>Query Transformation & Canonicalization</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem', fontSize: '0.82rem' }}>
              <div>
                <span style={{ color: '#94a3b8', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 600 }}>Original User Query:</span>
                <div style={{ color: '#f8fafc', fontWeight: 600, marginTop: '0.15rem' }}>"{originalQuery}"</div>
              </div>
              <div>
                <span style={{ color: '#94a3b8', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 600 }}>Canonical Symptom Formulation:</span>
                <div style={{ color: '#38bdf8', fontFamily: 'monospace', fontWeight: 600, marginTop: '0.15rem' }}>"{canonicalQuery}"</div>
              </div>
            </div>

            {qu?.reasoning_tags && qu.reasoning_tags.length > 0 && (
              <div style={{ marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid #334155' }}>
                <span style={{ color: '#94a3b8', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
                  Extracted Signals & Reasoning Tags:
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                  {qu.reasoning_tags.map((tag, i) => (
                    <span key={i} style={{ background: '#334155', padding: '0.2rem 0.55rem', borderRadius: '4px', fontSize: '0.72rem', color: '#cbd5e1' }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section: Final Match Summary */}
          <div style={{ marginBottom: '1.25rem', background: '#1e293b', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', color: '#4ade80', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <CheckCircle2 size={14} />
              <span>Resolved Problem & Selected Knowledge Record</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', fontSize: '0.82rem' }}>
              <div>
                <span style={{ color: '#94a3b8', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 600 }}>Selected Problem:</span>
                <div style={{ color: '#f8fafc', fontWeight: 700, marginTop: '0.15rem' }}>{selectedProblem}</div>
              </div>
              <div>
                <span style={{ color: '#94a3b8', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 600 }}>Problem ID / Goal:</span>
                <div style={{ color: '#38bdf8', fontFamily: 'monospace', marginTop: '0.15rem' }}>
                  {activeContext?.goal || qu?.target_problem_id || apiResponse?.final_problem_id || 'N/A'}
                </div>
              </div>
              <div>
                <span style={{ color: '#94a3b8', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 600 }}>Confidence Score:</span>
                <div style={{ color: '#4ade80', fontWeight: 800, marginTop: '0.15rem' }}>{matchConfidence}</div>
              </div>
            </div>
          </div>

          {/* Section: Multi-turn Clarification History (if present) */}
          {effectiveHistory.length > 0 && (
            <div style={{ marginBottom: '1.25rem', background: '#1e293b', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', color: '#facc15', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <HelpCircle size={14} />
                <span>Multi-Turn Clarification Conversation History</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {effectiveHistory.map((h, i) => (
                  <div key={i} style={{ background: '#0f172a', padding: '0.5rem 0.75rem', borderRadius: '6px', fontSize: '0.78rem', display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                    <span style={{ color: '#38bdf8', fontWeight: 800 }}>Turn {h.turn}:</span>
                    <span style={{ color: '#94a3b8' }}>Q: "{h.question}" &rarr;</span>
                    <span style={{ color: '#4ade80', fontWeight: 700 }}>Answer: {h.answer_label || h.user_text || h.answer_id}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section: Top Retrieval Candidates Table (BM25 + Semantic all-MiniLM-L6-v2 + RRF) */}
          {retrieval?.top_candidates && retrieval.top_candidates.length > 0 && (
            <div style={{ marginBottom: '1.25rem', background: '#1e293b', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#38bdf8', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <Cpu size={14} />
                  <span>Hybrid Retrieval Candidates (Neural all-MiniLM-L6-v2 + BM25 + RRF)</span>
                </div>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  Total Candidates: {retrieval.total_candidates_found}
                </span>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                      <th style={{ padding: '0.4rem 0.5rem', fontWeight: 700 }}>Problem ID</th>
                      <th style={{ padding: '0.4rem 0.5rem', fontWeight: 700 }}>Problem Statement</th>
                      <th style={{ padding: '0.4rem 0.5rem', fontWeight: 700 }}>Fused RRF</th>
                      <th style={{ padding: '0.4rem 0.5rem', fontWeight: 700 }}>BM25 Rank</th>
                      <th style={{ padding: '0.4rem 0.5rem', fontWeight: 700 }}>Semantic Rank</th>
                    </tr>
                  </thead>
                  <tbody>
                    {retrieval.top_candidates.map((c, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #283548' }}>
                        <td style={{ padding: '0.45rem 0.5rem', color: '#38bdf8', fontFamily: 'monospace' }}>{c.problem_id}</td>
                        <td style={{ padding: '0.45rem 0.5rem', color: '#e2e8f0' }}>{c.problem}</td>
                        <td style={{ padding: '0.45rem 0.5rem', color: '#4ade80', fontWeight: 800 }}>{c.fused_score.toFixed(4)}</td>
                        <td style={{ padding: '0.45rem 0.5rem', color: c.bm25_rank != null ? '#cbd5e1' : '#64748b' }}>
                          {c.bm25_rank != null ? `#${c.bm25_rank}` : '—'}
                        </td>
                        <td style={{ padding: '0.45rem 0.5rem', color: c.semantic_rank != null ? '#cbd5e1' : '#64748b' }}>
                          {c.semantic_rank != null ? `#${c.semantic_rank}` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Section: Collapsible Raw JSON Viewer */}
          <div style={{ borderTop: '1px solid #334155', paddingTop: '0.85rem', marginTop: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowRawJson(!showRawJson)}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#cbd5e1', padding: '0.4rem 0.85rem', fontSize: '0.78rem' }}
                aria-label={showRawJson ? 'Hide raw JSON response payload' : 'View full raw JSON response payload'}
              >
                <Cpu size={14} />
                <span>{showRawJson ? 'Hide Raw JSON' : 'View Full JSON Payload'}</span>
              </button>

              {showRawJson && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleCopyJson}
                  style={{ background: '#1e293b', border: '1px solid #334155', color: '#cbd5e1', padding: '0.4rem 0.85rem', fontSize: '0.78rem' }}
                  aria-label="Copy JSON payload to clipboard"
                >
                  {copied ? <Check size={14} color="#4ade80" /> : <Copy size={14} />}
                  <span>{copied ? 'Copied to Clipboard!' : 'Copy JSON'}</span>
                </button>
              )}
            </div>

            {showRawJson && (
              <pre
                style={{
                  background: '#020617',
                  padding: '1rem',
                  borderRadius: '8px',
                  marginTop: '0.75rem',
                  overflowX: 'auto',
                  fontSize: '0.75rem',
                  color: '#94a3b8',
                  maxHeight: '280px',
                  border: '1px solid #1e293b',
                  lineHeight: 1.45,
                }}
              >
                {JSON.stringify(
                  apiResponse || {
                    sessionId: effectiveSessionId,
                    turnCount: effectiveTurnCount,
                    maxTurns: effectiveMaxTurns,
                    clarificationHistory: effectiveHistory,
                    debugInfo: effectiveDebugInfo,
                    activeContext,
                  },
                  null,
                  2
                )}
              </pre>
            )}
          </div>
        </div>
      )}
    </aside>
  );
};
