import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp, Copy, Check, Cpu, Layers } from 'lucide-react';
import type { DiagnosticDebugMetadata, ClarificationTurnRecord } from '../types/api';

interface DebugPanelProps {
  debugInfo?: DiagnosticDebugMetadata | null;
  sessionId?: string | null;
  turnCount?: number;
  maxTurns?: number;
  clarificationHistory?: ClarificationTurnRecord[];
  isOpen: boolean;
  onToggle: () => void;
}

export const DebugPanel: React.FC<DebugPanelProps> = ({
  debugInfo,
  sessionId,
  turnCount,
  maxTurns,
  clarificationHistory,
  isOpen,
  onToggle,
}) => {
  const [showRawJson, setShowRawJson] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!debugInfo) {
    return null;
  }

  const { query_understanding, retrieval, latency } = debugInfo;

  const handleCopyJson = () => {
    const payload = {
      sessionId,
      turnCount,
      maxTurns,
      clarificationHistory,
      ...debugInfo,
    };
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="debug-panel" role="region" aria-label="Hackathon Technical Diagnostic Pipeline Inspector">
      <div className="debug-header" onClick={onToggle} style={{ cursor: 'pointer' }}>
        <div className="debug-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Terminal size={18} color="#38bdf8" />
          <span>Hackathon Diagnostic Pipeline Inspector (Phase 7 Multi-Turn)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#94a3b8', fontSize: '0.85rem' }}>
          <span>{isOpen ? 'Collapse Pipeline' : 'Inspect Pipeline'}</span>
          {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {isOpen && (
        <div className="debug-content" style={{ padding: '1.25rem', background: '#0f172a', color: '#f8fafc' }}>
          {/* Session & Turn Counter Status */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.25rem', padding: '0.75rem', background: '#1e293b', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Layers size={14} color="#38bdf8" />
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700 }}>TURN:</span>
              <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#f8fafc' }}>
                {turnCount ?? 1} / {maxTurns ?? 3}
              </span>
            </div>
            {sessionId && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginLeft: 'auto' }}>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Session ID:</span>
                <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#38bdf8' }}>{sessionId}</span>
              </div>
            )}
          </div>

          {/* Top Metrics Row */}
          <div className="debug-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div className="debug-item" style={{ background: '#1e293b', padding: '0.85rem', borderRadius: '8px' }}>
              <div className="debug-label" style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
                Query Understanding
              </div>
              <div className="debug-value" style={{ color: '#38bdf8', fontSize: '1.1rem', fontWeight: 800, marginTop: '0.2rem' }}>
                {query_understanding.domain ? query_understanding.domain.toUpperCase() : 'UNKNOWN'} ({(query_understanding.confidence * 100).toFixed(0)}%)
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
                Method: {query_understanding.rewrite_method}
              </div>
            </div>

            <div className="debug-item" style={{ background: '#1e293b', padding: '0.85rem', borderRadius: '8px' }}>
              <div className="debug-label" style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
                Decision Gating
              </div>
              <div className="debug-value" style={{ color: retrieval.decision === 'MATCH' ? '#4ade80' : '#f87171', fontSize: '1.1rem', fontWeight: 800, marginTop: '0.2rem' }}>
                {retrieval.decision} ({retrieval.confidence_level})
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
                Gate Threshold: {retrieval.similarity_threshold.toFixed(2)}
              </div>
            </div>

            <div className="debug-item" style={{ background: '#1e293b', padding: '0.85rem', borderRadius: '8px' }}>
              <div className="debug-label" style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
                Total Inference Latency
              </div>
              <div className="debug-value" style={{ color: '#facc15', fontSize: '1.1rem', fontWeight: 800, marginTop: '0.2rem' }}>
                {latency.total_pipeline_ms.toFixed(2)} ms
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
                QU: {latency.query_understanding_ms.toFixed(1)}ms • Ret: {latency.retrieval_ms.toFixed(1)}ms
              </div>
            </div>
          </div>

          {/* Canonical Rewrite Box */}
          <div style={{ marginBottom: '1rem' }}>
            <div className="debug-label" style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.35rem' }}>
              Canonical Symptom Mapping:
            </div>
            <div style={{ background: '#1e293b', padding: '0.6rem 0.85rem', borderRadius: '8px', color: '#38bdf8', fontFamily: 'monospace', fontSize: '0.85rem' }}>
              "{query_understanding.canonical_symptom || query_understanding.original_query}"
            </div>
          </div>

          {/* Multi-turn Clarification History */}
          {clarificationHistory && clarificationHistory.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <div className="debug-label" style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.35rem' }}>
                Multi-Turn Clarification History:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {clarificationHistory.map((h, i) => (
                  <div key={i} style={{ background: '#1e293b', padding: '0.5rem 0.75rem', borderRadius: '6px', fontSize: '0.78rem' }}>
                    <span style={{ color: '#38bdf8', fontWeight: 700 }}>Turn {h.turn}: </span>
                    <span style={{ color: '#e2e8f0' }}>{h.answer_label || h.user_text || h.answer_id}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reasoning Signals & Tags */}
          <div style={{ marginBottom: '1rem' }}>
            <div className="debug-label" style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.35rem' }}>
              Extracted Reasoning Signals:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
              {query_understanding.reasoning_tags.map((tag, i) => (
                <span key={i} style={{ background: '#334155', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', color: '#cbd5e1' }}>
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Hybrid Retrieval Candidates Table */}
          {retrieval.top_candidates.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <div className="debug-label" style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.35rem' }}>
                Top Retrieval Candidates (Neural all-MiniLM-L6-v2 + BM25 + RRF):
              </div>
              <div className="debug-code" style={{ overflowX: 'auto', background: '#1e293b', borderRadius: '8px', padding: '0.5rem' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                      <th style={{ padding: '0.4rem' }}>Problem ID</th>
                      <th style={{ padding: '0.4rem' }}>Problem Statement</th>
                      <th style={{ padding: '0.4rem' }}>Score</th>
                      <th style={{ padding: '0.4rem' }}>BM25 Rank</th>
                      <th style={{ padding: '0.4rem' }}>Semantic Rank</th>
                    </tr>
                  </thead>
                  <tbody>
                    {retrieval.top_candidates.map((c, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #283548' }}>
                        <td style={{ padding: '0.4rem', color: '#38bdf8', fontFamily: 'monospace' }}>{c.problem_id}</td>
                        <td style={{ padding: '0.4rem' }}>{c.problem}</td>
                        <td style={{ padding: '0.4rem', color: '#4ade80', fontWeight: 700 }}>{c.fused_score.toFixed(4)}</td>
                        <td style={{ padding: '0.4rem', color: '#94a3b8' }}>{c.bm25_rank ?? '—'}</td>
                        <td style={{ padding: '0.4rem', color: '#94a3b8' }}>{c.semantic_rank ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Collapsible Raw JSON Viewer */}
          <div style={{ borderTop: '1px solid #334155', paddingTop: '0.75rem', marginTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowRawJson(!showRawJson)}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#cbd5e1', padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
              >
                <Cpu size={14} />
                <span>{showRawJson ? 'Hide Raw JSON' : 'View Full JSON Payload'}</span>
              </button>

              {showRawJson && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleCopyJson}
                  style={{ background: '#1e293b', border: '1px solid #334155', color: '#cbd5e1', padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                >
                  {copied ? <Check size={14} color="#4ade80" /> : <Copy size={14} />}
                  <span>{copied ? 'Copied!' : 'Copy JSON'}</span>
                </button>
              )}
            </div>

            {showRawJson && (
              <pre style={{ background: '#020617', padding: '1rem', borderRadius: '8px', marginTop: '0.75rem', overflowX: 'auto', fontSize: '0.75rem', color: '#94a3b8', maxHeight: '250px' }}>
                {JSON.stringify({ sessionId, turnCount, maxTurns, clarificationHistory, ...debugInfo }, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
