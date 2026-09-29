import React, { useState } from 'react';
import { Battery, Eye, Camera, Cpu, HelpCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import type { ClarificationOption, ClarificationQuestion } from '../types/api';

interface ClarificationViewProps {
  clarification: ClarificationQuestion;
  isLoading: boolean;
  onSelectOption: (option: ClarificationOption) => void;
  onSubmitCustom: (text: string) => void;
  onCancel: () => void;
}

export const ClarificationView: React.FC<ClarificationViewProps> = ({
  clarification,
  isLoading,
  onSelectOption,
  onSubmitCustom,
  onCancel,
}) => {
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [customText, setCustomText] = useState('');
  const [isCustomMode, setIsCustomMode] = useState(false);

  const getDomainInfo = (domain: string) => {
    switch (domain) {
      case 'battery':
        return { label: 'Battery & Power', icon: Battery, domainClass: 'battery' };
      case 'display':
        return { label: 'Display & Touch', icon: Eye, domainClass: 'display' };
      case 'camera':
        return { label: 'Camera & Media', icon: Camera, domainClass: 'camera' };
      case 'performance':
        return { label: 'Performance & System', icon: Cpu, domainClass: 'performance' };
      default:
        return { label: 'Device', icon: HelpCircle, domainClass: 'performance' };
    }
  };

  const domainInfo = getDomainInfo(clarification.domain);
  const DomainIcon = domainInfo.icon;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isCustomMode && customText.trim()) {
      onSubmitCustom(customText.trim());
    } else if (selectedOptionId) {
      const opt = clarification.options.find((o) => o.id === selectedOptionId);
      if (opt) {
        onSelectOption(opt);
      }
    }
  };

  const isSubmitDisabled =
    isLoading || (!selectedOptionId && (!isCustomMode || !customText.trim()));

  return (
    <div className="clarification-card" role="region" aria-label="Disambiguation Step">
      {/* Header with Domain Badge & Step Marker */}
      <div className="clarification-header">
        <span className={`domain-pill ${domainInfo.domainClass}`}>
          <DomainIcon size={14} />
          <span>{domainInfo.label}</span>
        </span>
        <span className="clarification-step-tag">
          Step 2 of 3: Disambiguation
        </span>
      </div>

      {/* Main Question & Prompt */}
      <h2 className="clarification-title">
        {clarification.question}
      </h2>
      <p className="clarification-prompt">
        {clarification.prompt}
      </p>

      {/* Structured Option Cards */}
      <form onSubmit={handleSubmit}>
        <div className="clarification-options-list" role="radiogroup" aria-label="Clarification options">
          {clarification.options.map((option, idx) => {
            const isSelected = selectedOptionId === option.id && !isCustomMode;
            return (
              <div
                key={option.id}
                role="radio"
                aria-checked={isSelected}
                tabIndex={0}
                onClick={() => {
                  setSelectedOptionId(option.id);
                  setIsCustomMode(false);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedOptionId(option.id);
                    setIsCustomMode(false);
                  }
                }}
                className={`clarification-option-card ${isSelected ? 'selected' : ''}`}
              >
                <div className="clarification-radio">
                  {isSelected && <div className="clarification-radio-dot" />}
                </div>

                <div className="clarification-option-content">
                  <div className="clarification-option-top">
                    <span className="clarification-option-label">
                      {option.label}
                    </span>
                    <span className="clarification-option-index">
                      Option {idx + 1}
                    </span>
                  </div>
                  {option.description && (
                    <p className="clarification-option-desc">
                      {option.description}
                    </p>
                  )}
                </div>
              </div>
            );
          })}

          {/* Custom User Description Option */}
          <div
            role="radio"
            aria-checked={isCustomMode}
            tabIndex={0}
            onClick={() => setIsCustomMode(true)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setIsCustomMode(true);
              }
            }}
            className={`clarification-custom-card ${isCustomMode ? 'selected' : ''}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div className="clarification-radio">
                {isCustomMode && <div className="clarification-radio-dot" />}
              </div>
              <span className="clarification-option-label">
                Describe in your own words
              </span>
            </div>

            {isCustomMode && (
              <textarea
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                placeholder="e.g. It happens right after opening Instagram or playing heavy 3D games..."
                className="clarification-textarea"
                rows={2}
                autoFocus
                onClick={(e) => e.stopPropagation()}
              />
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="clarification-actions">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="btn-secondary"
            aria-label="Back to search"
          >
            <ArrowLeft size={16} />
            <span>Back to Search</span>
          </button>

          <button
            type="submit"
            disabled={isSubmitDisabled}
            className="btn-primary"
            aria-label="Confirm and get resolution"
          >
            <span>{isLoading ? 'Refining Diagnosis...' : 'Confirm & Get Resolution'}</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </form>
    </div>
  );
};
