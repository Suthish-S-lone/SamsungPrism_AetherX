import React from 'react';
import { Sparkles, Cpu, Layers } from 'lucide-react';

interface LoadingStateProps {
  query: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ query }) => {
  return (
    <div className="card loading-box">
      <div className="spinner" />
      <h3 className="loading-text">SmartGuide is analyzing your issue...</h3>
      <p className="loading-subtext">"{query}"</p>

      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '1.5rem',
          marginTop: '1.5rem',
          fontSize: '0.85rem',
          color: 'var(--text-secondary)',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Sparkles size={14} color="#0381fe" />
          Understanding Symptoms
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Layers size={14} color="#0381fe" />
          Neural Hybrid Search
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Cpu size={14} color="#0381fe" />
          Resolving Deeplinks
        </span>
      </div>
    </div>
  );
};
