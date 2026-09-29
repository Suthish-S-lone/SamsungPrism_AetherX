import React from 'react';
import { ExternalLink, CheckCircle2, ChevronLeft, Wrench, ShieldCheck, ArrowRight, ArrowLeft, Info } from 'lucide-react';
import type { Action, Context } from '../types/api';

interface GuidedWorkflowProps {
  context: Context;
  currentActionIndex: number;
  completedActions: number[];
  onOpenDeeplink: (action: Action) => void;
  onCompleteAction: (actionIndex: number) => void;
  onFinishWorkflow: () => void;
  onBackToDiagnosis: () => void;
}

export const GuidedWorkflow: React.FC<GuidedWorkflowProps> = ({
  context,
  currentActionIndex,
  completedActions,
  onOpenDeeplink,
  onCompleteAction,
  onFinishWorkflow,
  onBackToDiagnosis,
}) => {
  const currentAction = context.actions[currentActionIndex] || context.actions[0];
  const totalActions = context.actions.length;
  const isFirstAction = currentActionIndex === 0;
  const isLastAction = currentActionIndex === totalActions - 1;
  const isCompleted = completedActions.includes(currentActionIndex);

  return (
    <div className="card" role="region" aria-label="Guided Troubleshooting Workflow">
      {/* Top Workflow Header & Step Counter */}
      <div className="workflow-progress">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="step-indicator-text" style={{ fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              STEP {currentActionIndex + 1} OF {totalActions}
            </span>
            <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: '6px', background: 'var(--bg-secondary)', color: 'var(--text-muted)' }}>
              {isCompleted ? '✓ Completed' : 'In Progress'}
            </span>
          </div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.3rem', color: 'var(--text-primary)' }}>
            {context.goal}
          </h2>
        </div>

        <button
          className="btn-secondary"
          onClick={onBackToDiagnosis}
          style={{ padding: '0.4rem 0.85rem', fontSize: '0.85rem' }}
          aria-label="Return to diagnosis card"
        >
          <ChevronLeft size={16} />
          <span>Back to Diagnosis</span>
        </button>
      </div>

      {/* Step Tracker Pills */}
      <div style={{ display: 'flex', gap: '0.4rem', margin: '1rem 0 1.25rem' }}>
        {context.actions.map((_, idx) => {
          const isDone = completedActions.includes(idx);
          const isCurrent = idx === currentActionIndex;
          return (
            <div
              key={idx}
              style={{
                flex: 1,
                height: '6px',
                borderRadius: '3px',
                background: isDone
                  ? 'var(--success)'
                  : isCurrent
                  ? 'var(--primary)'
                  : 'var(--border-color)',
                transition: 'background 0.3s ease',
              }}
              title={`Step ${idx + 1}: ${context.actions[idx].action_name}`}
            />
          );
        })}
      </div>

      {/* Identified Issue & Recommended Action */}
      <div style={{ margin: '1rem 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
          <Wrench size={18} color="var(--primary)" />
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
            {currentAction.action_name}
          </h3>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6 }}>
          {currentAction.description}
        </p>
      </div>

      {/* Technical Rationale Callout */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.6rem',
          padding: '0.85rem 1rem',
          borderRadius: '10px',
          background: 'rgba(3, 129, 254, 0.06)',
          borderLeft: '4px solid var(--primary)',
          margin: '1rem 0 1.25rem',
        }}
      >
        <Info size={18} color="var(--primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          <strong>Why this step:</strong> This setting directly addresses the issue you described. Adjusting it should help resolve the problem.
        </div>
      </div>

      {/* Simulated Deeplink Target Card */}
      <div className="deeplink-box">
        <div className="deeplink-info">
          <span style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--primary)', letterSpacing: '0.05em' }}>
            Target Settings Destination (Simulated)
          </span>
          <span className="deeplink-target" style={{ fontWeight: 700, fontSize: '1rem' }}>
            {currentAction.target_screen}
          </span>
          {currentAction.deeplink && (
            <span className="deeplink-uri" style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {currentAction.deeplink}
            </span>
          )}
        </div>

        <button
          className="btn-primary"
          onClick={() => onOpenDeeplink(currentAction)}
          style={{ padding: '0.65rem 1.2rem', fontSize: '0.9rem' }}
          aria-label={`Open simulated setting for ${currentAction.target_screen}`}
        >
          <ExternalLink size={16} />
          <span>Open Simulated Setting</span>
        </button>
      </div>

      {/* Step-by-Step Instruction Checklist */}
      <div style={{ marginTop: '1.5rem' }}>
        <h4 style={{ fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
          Action Instructions:
        </h4>
        <ul className="step-checklist" style={{ listStyle: 'none', padding: 0 }}>
          {currentAction.steps.map((step, idx) => (
            <li key={idx} className="step-item">
              <span className="step-number">{idx + 1}</span>
              <span style={{ fontSize: '0.92rem', color: 'var(--text-primary)' }}>{step.text}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Action Navigation & Completion Footer */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: '2rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid var(--border-light)',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <span style={{ fontSize: '0.85rem', color: isCompleted ? 'var(--success)' : 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          {isCompleted ? <CheckCircle2 size={16} color="var(--success)" /> : <ShieldCheck size={16} />}
          {isCompleted ? 'Step verified in prototype simulation' : 'Launch simulator to test setting'}
        </span>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {!isFirstAction && (
            <button
              className="btn-secondary"
              onClick={() => onCompleteAction(currentActionIndex - 1)}
              style={{ padding: '0.6rem 1rem', fontSize: '0.9rem' }}
              aria-label="Go to previous action step"
            >
              <ArrowLeft size={16} />
              <span>Previous Step</span>
            </button>
          )}

          <button
            className="btn-primary"
            onClick={() => {
              onCompleteAction(currentActionIndex);
              if (isLastAction) {
                onFinishWorkflow();
              }
            }}
            aria-label={isLastAction ? 'Finish troubleshooting workflow' : 'Complete step and go to next action'}
          >
            <CheckCircle2 size={18} />
            <span>{isLastAction ? 'Complete & Verify' : 'Next Step'}</span>
            {!isLastAction && <ArrowRight size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
};
