import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, RefreshCw, Activity, MapPin, MessageSquare, ArrowRight, ShieldAlert } from 'lucide-react';
import type { Context } from '../types/api';

interface ResolutionFeedbackProps {
  context: Context;
  onNewDiagnosis: () => void;
  onRetryDiagnosis: () => void;
}

export const ResolutionFeedback: React.FC<ResolutionFeedbackProps> = ({
  context,
  onNewDiagnosis,
  onRetryDiagnosis,
}) => {
  const [resolvedState, setResolvedState] = useState<'prompt' | 'resolved' | 'escalate'>('prompt');
  const [activeEscalationSim, setActiveEscalationSim] = useState<string | null>(null);

  if (resolvedState === 'resolved') {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'var(--success-bg)',
            color: 'var(--success)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem',
          }}
        >
          <CheckCircle2 size={36} />
        </div>

        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)' }}>
          Problem Resolved!
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '500px', margin: '0.75rem auto 2rem', fontSize: '1rem', lineHeight: 1.5 }}>
          SmartGuide successfully completed the recommended troubleshooting steps for <strong>"{context.goal}"</strong>.
        </p>

        <div
          style={{
            background: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem',
            maxWidth: '450px',
            margin: '0 auto 2rem',
            textAlign: 'left',
          }}
        >
          <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            Workflow Completed
          </div>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <span>✓ Symptom Understanding & Classification</span>
            <span>✓ Settings Navigation & Simulation</span>
            <span>✓ Action Step Execution Verified</span>
          </div>
        </div>

        <button className="btn-primary" onClick={onNewDiagnosis} style={{ margin: '0 auto' }}>
          <RefreshCw size={18} />
          <span>Start Another Diagnosis</span>
        </button>
      </div>
    );
  }

  if (resolvedState === 'escalate') {
    return (
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <AlertTriangle size={28} color="#f59e0b" />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Need Further Assistance?</h2>
        </div>

        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', lineHeight: 1.6 }}>
          If the initial settings actions did not completely resolve <strong>"{context.goal}"</strong>, deeper hardware diagnostics or simulated Samsung Care escalation options are available below.
        </p>

        {/* 3 Simulated Escalation Channels */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          {/* 1. Samsung Members Diagnostics */}
          <div
            className="setting-card"
            style={{
              cursor: 'pointer',
              padding: '1.25rem',
              border: activeEscalationSim === 'diagnostics' ? '2px solid var(--primary)' : '1px solid var(--border-color)',
            }}
            onClick={() => setActiveEscalationSim(activeEscalationSim === 'diagnostics' ? null : 'diagnostics')}
          >
            <div style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={18} color="var(--primary)" />
              <span>Samsung Members Diagnostics</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.4rem', lineHeight: 1.4 }}>
              Run comprehensive automated hardware diagnostics for sensors, battery health, and touchscreen response.
            </p>
            <span style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 600, display: 'inline-block', marginTop: '0.5rem' }}>
              {activeEscalationSim === 'diagnostics' ? '▲ Hide Details' : '▶ Simulate Test'}
            </span>
          </div>

          {/* 2. Service Center Appointment */}
          <div
            className="setting-card"
            style={{
              cursor: 'pointer',
              padding: '1.25rem',
              border: activeEscalationSim === 'service_center' ? '2px solid var(--primary)' : '1px solid var(--border-color)',
            }}
            onClick={() => setActiveEscalationSim(activeEscalationSim === 'service_center' ? null : 'service_center')}
          >
            <div style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <MapPin size={18} color="var(--primary)" />
              <span>Service Center Appointment</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.4rem', lineHeight: 1.4 }}>
              Locate authorized repair centers and schedule a physical technician inspection.
            </p>
            <span style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 600, display: 'inline-block', marginTop: '0.5rem' }}>
              {activeEscalationSim === 'service_center' ? '▲ Hide Details' : '▶ View Locations'}
            </span>
          </div>

          {/* 3. Live Support Chat */}
          <div
            className="setting-card"
            style={{
              cursor: 'pointer',
              padding: '1.25rem',
              border: activeEscalationSim === 'chat' ? '2px solid var(--primary)' : '1px solid var(--border-color)',
            }}
            onClick={() => setActiveEscalationSim(activeEscalationSim === 'chat' ? null : 'chat')}
          >
            <div style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <MessageSquare size={18} color="var(--primary)" />
              <span>Live Support Chat</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.4rem', lineHeight: 1.4 }}>
              Transfer diagnostic telemetry directly to a simulated Samsung technical support specialist.
            </p>
            <span style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 600, display: 'inline-block', marginTop: '0.5rem' }}>
              {activeEscalationSim === 'chat' ? '▲ Hide Details' : '▶ Connect Agent'}
            </span>
          </div>
        </div>

        {/* Active Escalation Simulator Display */}
        {activeEscalationSim && (
          <div className="card" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', marginBottom: '1.5rem', padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              <ShieldAlert size={16} color="var(--primary)" />
              <span>Prototype Simulated Escalation Mode</span>
            </div>

            {activeEscalationSim === 'diagnostics' && (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <div>🔬 <strong>Simulated Test:</strong> Battery Health Status = Normal (94% Efficiency)</div>
                <div>📡 <strong>Sensor Check:</strong> Ambient Light Sensor = Pass, Proximity = Pass</div>
                <div>⚡ <strong>Power Circuit:</strong> Fast Charging IC = Pass</div>
                <div style={{ marginTop: '0.5rem', color: 'var(--success)', fontWeight: 700 }}>✓ All hardware diagnostic self-tests PASSED (Simulation)</div>
              </div>
            )}

            {activeEscalationSim === 'service_center' && (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <div>📍 <strong>Samsung Experience Store & Service:</strong> 123 Tech Park Blvd (2.1 mi)</div>
                <div>⏱️ <strong>Next Available Walk-in Slot:</strong> Today at 4:30 PM</div>
                <div>📞 <strong>Support Line:</strong> 1-800-SAMSUNG (Prototype Simulation)</div>
              </div>
            )}

            {activeEscalationSim === 'chat' && (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <div>💬 <strong>Agent Status:</strong> Connected to SmartCare Specialist (Simulation)</div>
                <div>📋 <strong>Pre-filled Context:</strong> Issue = {context.goal}, Target = {context.actions[0]?.target_screen}</div>
                <div>💬 <em>"Hello! I see you recently ran troubleshooting for {context.goal}. How can I help further?"</em></div>
              </div>
            )}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border-light)' }}>
          <button className="btn-secondary" onClick={onRetryDiagnosis}>
            <RefreshCw size={16} />
            <span>Try Another Query</span>
          </button>
          <button className="btn-primary" onClick={onNewDiagnosis}>
            <span>New Troubleshooting Session</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ textAlign: 'center', padding: '2.5rem 1.5rem' }}>
      <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.5rem' }}>
        Did this solve your problem?
      </h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '2rem' }}>
        Please let SmartGuide know if the guided settings actions resolved <strong>"{context.goal}"</strong>.
      </p>

      <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <button
          className="btn-primary"
          style={{ background: 'var(--success)', padding: '0.85rem 1.75rem', fontSize: '1rem' }}
          onClick={() => setResolvedState('resolved')}
          aria-label="Confirm issue was fixed"
        >
          <CheckCircle2 size={20} />
          <span>Yes, it's fixed!</span>
        </button>

        <button
          className="btn-secondary"
          style={{ padding: '0.85rem 1.75rem', fontSize: '1rem' }}
          onClick={() => setResolvedState('escalate')}
          aria-label="Report issue is still occurring"
        >
          <span>No, I still need help</span>
        </button>
      </div>
    </div>
  );
};
