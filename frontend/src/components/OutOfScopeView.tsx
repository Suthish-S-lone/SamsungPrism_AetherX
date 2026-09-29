import React from 'react';
import { HelpCircle, Battery, Eye, Camera, Cpu, RefreshCw } from 'lucide-react';

interface OutOfScopeViewProps {
  query: string;
  fallbackMessage?: string | null;
  onTryAgain: () => void;
  onSelectSupportedExample: (exampleQuery: string) => void;
}

export const OutOfScopeView: React.FC<OutOfScopeViewProps> = ({
  query,
  fallbackMessage,
  onTryAgain,
  onSelectSupportedExample,
}) => {
  return (
    <div className="card">
      <div style={{ textAlign: 'center', padding: '1rem 0 2rem' }}>
        <div
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: 'var(--primary-light)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem',
          }}
        >
          <HelpCircle size={32} />
        </div>

        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
          This isn't something SmartGuide can diagnose
        </h2>

        <p style={{ color: 'var(--text-secondary)', maxWidth: '560px', margin: '0 auto 1.5rem', fontSize: '0.95rem', lineHeight: 1.6 }}>
          {fallbackMessage ||
            'SmartGuide is designed specifically for Samsung device troubleshooting (battery, display, camera, and performance). Your query appears outside this domain.'}
        </p>

        <div style={{ background: '#f8fafc', padding: '0.75rem 1.25rem', borderRadius: 'var(--radius-md)', display: 'inline-block', border: '1px solid var(--border-light)' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Received Query:</span>{' '}
          <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>"{query}"</strong>
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '1.5rem' }}>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '1rem' }}>
          SmartGuide Currently Supports:
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <div
            className="setting-card"
            style={{ cursor: 'pointer' }}
            onClick={() => onSelectSupportedExample('My battery drains very quickly during normal use')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, color: '#0369a1' }}>
              <Battery size={18} />
              <span>Battery & Power</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
              Drain, slow charging, overheating, power saving
            </p>
          </div>

          <div
            className="setting-card"
            style={{ cursor: 'pointer' }}
            onClick={() => onSelectSupportedExample('My screen brightness changes unexpectedly')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, color: '#6d28d9' }}>
              <Eye size={18} />
              <span>Display & Touch</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
              Brightness, screen timeout, gestures, touch delay
            </p>
          </div>

          <div
            className="setting-card"
            style={{ cursor: 'pointer' }}
            onClick={() => onSelectSupportedExample('My camera photos look blurry and out of focus')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, color: '#b45309' }}>
              <Camera size={18} />
              <span>Camera & Media</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
              Freezing, blurry photos, permissions, storage
            </p>
          </div>

          <div
            className="setting-card"
            style={{ cursor: 'pointer' }}
            onClick={() => onSelectSupportedExample('My phone feels sluggish and apps freeze')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, color: '#15803d' }}>
              <Cpu size={18} />
              <span>Performance</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
              Sluggishness, low memory, storage full, app lag
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button className="btn-primary" onClick={onTryAgain}>
            <RefreshCw size={16} />
            <span>Try Describing a Device Issue</span>
          </button>
        </div>
      </div>
    </div>
  );
};
