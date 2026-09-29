import React from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';

interface ErrorViewProps {
  errorMessage: string;
  onRetry: () => void;
}

export const ErrorView: React.FC<ErrorViewProps> = ({ errorMessage, onRetry }) => {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: 'var(--danger-bg)',
          color: 'var(--danger)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1.25rem',
        }}
      >
        <WifiOff size={28} />
      </div>

      <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
        SmartGuide couldn't connect to the diagnostic service
      </h2>

      <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto 1.5rem', fontSize: '0.95rem', lineHeight: 1.6 }}>
        The FastAPI backend at <code>http://127.0.0.1:8000</code> may be starting up or temporarily offline.
      </p>

      <div
        style={{
          background: '#f8fafc',
          border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.75rem',
          maxWidth: '480px',
          margin: '0 auto 2rem',
          fontSize: '0.8rem',
          color: 'var(--danger)',
          fontFamily: 'monospace',
          textAlign: 'left',
          overflowX: 'auto',
        }}
      >
        {errorMessage}
      </div>

      <button className="btn-primary" onClick={onRetry} style={{ margin: '0 auto' }}>
        <RefreshCw size={16} />
        <span>Try Again</span>
      </button>
    </div>
  );
};
