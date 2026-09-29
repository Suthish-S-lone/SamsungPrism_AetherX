import React from 'react';
import { Battery, Eye, Camera, Cpu, ArrowRight, ShieldCheck } from 'lucide-react';
import type { Context, DiagnosticDebugMetadata } from '../types/api';

interface DiagnosisCardProps {
  context: Context;
  debugInfo?: DiagnosticDebugMetadata | null;
  onStartWorkflow: () => void;
  onSelectAlternative?: (altContext: Context) => void;
  allContexts?: Context[];
}

export const DiagnosisCard: React.FC<DiagnosisCardProps> = ({
  context,
  debugInfo,
  onStartWorkflow,
}) => {
  const scorePercent = Math.round(context.score * 100);
  const isHighConfidence = context.score >= 0.70;

  // Infer domain from goal/title
  const goalLower = context.goal.toLowerCase();
  let domain = 'Device';
  let DomainIcon = Cpu;
  let domainClass = 'performance';

  if (goalLower.includes('battery') || goalLower.includes('charge') || goalLower.includes('power') || goalLower.includes('hot')) {
    domain = 'Battery & Power';
    DomainIcon = Battery;
    domainClass = 'battery';
  } else if (goalLower.includes('screen') || goalLower.includes('display') || goalLower.includes('touch') || goalLower.includes('gesture') || goalLower.includes('brightness')) {
    domain = 'Display & Touch';
    DomainIcon = Eye;
    domainClass = 'display';
  } else if (goalLower.includes('camera') || goalLower.includes('photo') || goalLower.includes('video') || goalLower.includes('lens')) {
    domain = 'Camera & Media';
    DomainIcon = Camera;
    domainClass = 'camera';
  } else {
    domain = 'Performance & System';
    DomainIcon = Cpu;
    domainClass = 'performance';
  }

  // Explanation text derived from understanding and goal
  const explanation = debugInfo?.query_understanding?.reasoning_tags?.[2] ||
    `Based on your description, SmartGuide identified symptoms associated with "${context.goal}". A targeted resolution pathway is ready.`;

  const totalSteps = context.actions.reduce((acc, act) => acc + act.steps.length, 0);

  return (
    <div className="card">
      <div className="diagnosis-header">
        <div>
          <span className={`domain-pill ${domainClass}`}>
            <DomainIcon size={14} />
            <span>{domain}</span>
          </span>
          <h2 className="diagnosis-title">{context.title}</h2>
        </div>

        <div className={`confidence-badge ${isHighConfidence ? 'high' : 'medium'}`}>
          <ShieldCheck size={16} />
          <span>{scorePercent}% Match Confidence</span>
        </div>
      </div>

      <div className="explanation-card">
        <div className="explanation-label">Why SmartGuide Recommends This:</div>
        <p className="explanation-text">{explanation}</p>
      </div>

      <div style={{ margin: '1.5rem 0' }}>
        <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
          Recommended Resolution Actions ({context.actions.length}):
        </h4>
        {context.actions.map((action, idx) => (
          <div
            key={idx}
            style={{
              background: '#f8fafc',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-md)',
              padding: '1rem',
              marginBottom: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)' }}>
                {action.action_name}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                Target: {action.target_screen} • {action.steps.length} guided steps
              </div>
            </div>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                background: 'var(--bg-subtle)',
                padding: '0.25rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              {action.category}
            </span>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2rem' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Step-by-step guidance • {totalSteps} total actions
        </span>
        <button className="btn-primary" onClick={onStartWorkflow}>
          <span>Start Guided Troubleshooting</span>
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
};
