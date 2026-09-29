import React, { useState } from 'react';
import { Search, Sparkles, Battery, Eye, Camera, Cpu, ArrowRight, X, PlayCircle, HelpCircle } from 'lucide-react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

interface DemoScenario {
  domain: 'Battery' | 'Display' | 'Camera' | 'Performance' | 'Out-of-Scope' | 'Multi-Turn';
  label: string;
  icon: React.ComponentType<{ size?: number; color?: string; className?: string }>;
  query: string;
  expectedOutcome: string;
  isOutOfScope?: boolean;
  isMultiTurn?: boolean;
}

const EVALUATOR_DEMO_SCENARIOS: DemoScenario[] = [
  {
    domain: 'Multi-Turn',
    label: 'Thermal Ambiguity (Phase 6)',
    icon: Sparkles,
    query: 'My phone gets really hot',
    expectedOutcome: 'Triggers multi-turn clarification options to pinpoint exact thermal cause',
    isMultiTurn: true,
  },
  {
    domain: 'Battery',
    label: 'Battery Drain',
    icon: Battery,
    query: 'My phone battery is draining really fast even when I barely use it.',
    expectedOutcome: 'Diagnoses idle battery consumption and guides background usage limits',
  },
  {
    domain: 'Display',
    label: 'Adaptive Brightness',
    icon: Eye,
    query: 'The screen brightness keeps changing on its own.',
    expectedOutcome: 'Identifies sensor-driven auto-brightness and provides adjustment steps',
  },
  {
    domain: 'Camera',
    label: 'Camera Freezing',
    icon: Camera,
    query: 'The camera freezes whenever I try to record a video.',
    expectedOutcome: 'Detects camera app lockup and resolves camera cache reset',
  },
  {
    domain: 'Performance',
    label: 'App Sluggishness',
    icon: Cpu,
    query: 'My phone becomes extremely slow when I have many apps open.',
    expectedOutcome: 'Detects RAM / memory pressure and guides Device Care optimization',
  },
  {
    domain: 'Out-of-Scope',
    label: 'Non-Troubleshooting Query',
    icon: HelpCircle,
    query: 'Will it rain tomorrow?',
    expectedOutcome: 'Demonstrates safe boundary filtering and supported domain guidance',
    isOutOfScope: true,
  },
];

export const QueryInput: React.FC<QueryInputProps> = ({ onSubmit, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handleSelectScenario = (scenarioQuery: string) => {
    setQuery(scenarioQuery);
    onSubmit(scenarioQuery);
  };

  return (
    <div className="card">
      <div className="hero-section">
        <div className="hero-badge" aria-label="Prototype Identification">
          <Sparkles size={14} />
          <span>Samsung PRISM Theme 2 — Smart Guided Troubleshooting Prototype</span>
        </div>
        <h1 className="hero-title">What problem are you experiencing?</h1>
        <p className="hero-subtitle">
          Describe any Samsung device issue in natural, colloquial language. SmartGuide will understand your complaint, identify the technical resolution, and guide you through simulated settings actions.
        </p>
      </div>

      <form onSubmit={handleSubmit} role="search">
        <div className="search-container">
          <Search size={22} color="#8c9ba5" aria-hidden="true" />
          <input
            type="text"
            className="search-input"
            placeholder="e.g. My phone dies before lunch every day..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
            aria-label="Describe your device problem"
            autoFocus
          />
          {query && (
            <button
              type="button"
              className="btn-icon"
              style={{ border: 'none', padding: '0.25rem' }}
              onClick={() => setQuery('')}
              aria-label="Clear query"
            >
              <X size={18} />
            </button>
          )}
          <button
            type="submit"
            className="btn-primary"
            disabled={!query.trim() || isLoading}
            aria-label="Diagnose device problem"
          >
            <span>{isLoading ? 'Analyzing...' : 'Diagnose'}</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </form>

      {/* Evaluator Demo Scenarios Section */}
      <div className="demo-scenarios-container" style={{ marginTop: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <PlayCircle size={16} color="var(--primary)" />
          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Evaluator Demo Scenarios (One-Click Test):
          </span>
        </div>

        <div className="demo-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
          {EVALUATOR_DEMO_SCENARIOS.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                type="button"
                className={`demo-card-btn ${item.isOutOfScope ? 'out-of-scope-demo' : ''}`}
                onClick={() => handleSelectScenario(item.query)}
                disabled={isLoading}
                aria-label={`Test scenario: ${item.label}`}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  padding: '0.85rem 1rem',
                  borderRadius: '12px',
                  background: item.isOutOfScope ? '#fff5f5' : 'var(--bg-secondary)',
                  border: item.isOutOfScope ? '1px solid #fed7d7' : '1px solid var(--border-color)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem' }}>
                  <Icon size={14} color={item.isOutOfScope ? '#e53e3e' : '#0381fe'} />
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', color: item.isOutOfScope ? '#c53030' : 'var(--primary)' }}>
                    {item.domain}
                  </span>
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                  "{item.query}"
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  {item.expectedOutcome}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="disclaimer-banner" style={{ marginTop: '1.5rem' }}>
        <strong>Development Prototype Notice:</strong> SmartGuide operates on development datasets with local Neural Hybrid Retrieval and simulated One UI settings. All deep links use the safe <code>prototype://</code> scheme.
      </div>
    </div>
  );
};
