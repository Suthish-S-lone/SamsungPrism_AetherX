import React from 'react';
import { Smartphone, RefreshCw } from 'lucide-react';

interface HeaderProps {
  onNewDiagnosis: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onNewDiagnosis }) => {
  return (
    <header className="app-header">
      <div className="header-inner">
        <div
          className="brand-group"
          onClick={onNewDiagnosis}
          role="button"
          tabIndex={0}
          aria-label="SmartGuide Home"
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onNewDiagnosis();
            }
          }}
        >
          <span className="brand-badge">SAMSUNG</span>
          <div className="brand-title">
            <Smartphone size={22} color="#0381fe" />
            <span>SmartGuide</span>
          </div>
          <span className="brand-prototype-tag">Prototype Simulation</span>
        </div>

        <div className="header-actions">
          <button
            type="button"
            className="btn-icon"
            onClick={onNewDiagnosis}
            title="Start a new troubleshooting session"
            aria-label="Start a new troubleshooting session"
          >
            <RefreshCw size={15} />
            <span>New Diagnosis</span>
          </button>
        </div>
      </div>
    </header>
  );
};
