import React from 'react';
import { Smartphone, RefreshCw, Terminal } from 'lucide-react';

interface HeaderProps {
  backendOnline: boolean;
  debugMode: boolean;
  onToggleDebug: () => void;
  onNewDiagnosis: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  backendOnline,
  debugMode,
  onToggleDebug,
  onNewDiagnosis,
}) => {
  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="brand-group" onClick={onNewDiagnosis}>
          <span className="brand-badge">SAMSUNG</span>
          <div className="brand-title">
            <Smartphone size={22} color="#0381fe" />
            <span>SmartGuide</span>
          </div>
          <span className="brand-prototype-tag">Prototype Simulation</span>
        </div>

        <div className="header-actions">
          <div className="status-badge" title={backendOnline ? 'Backend service online' : 'Backend offline'}>
            <span className={`status-dot ${backendOnline ? '' : 'offline'}`} />
            <span>{backendOnline ? 'Ready' : 'Offline'}</span>
          </div>

          <button
            className={`btn-icon ${debugMode ? 'active' : ''}`}
            onClick={onToggleDebug}
            title="Toggle Technical Diagnostic Pipeline"
          >
            <Terminal size={16} />
            <span>{debugMode ? 'Diagnostics ON' : 'Diagnostics'}</span>
          </button>

          <button
            className="btn-icon"
            onClick={onNewDiagnosis}
            title="Start a new troubleshooting session"
          >
            <RefreshCw size={15} />
            <span>New Diagnosis</span>
          </button>
        </div>
      </div>
    </header>
  );
};
