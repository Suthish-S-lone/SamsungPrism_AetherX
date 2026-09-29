import React, { useState } from 'react';
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

  const getDomainBadge = (domain: string) => {
    switch (domain) {
      case 'battery':
        return { label: 'Battery & Thermal', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800' };
      case 'display':
        return { label: 'Display & Touch', color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-400 border-indigo-300 dark:border-indigo-800' };
      case 'camera':
        return { label: 'Camera & Vision', color: 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border-rose-300 dark:border-rose-800' };
      case 'performance':
        return { label: 'Performance & Memory', color: 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border-amber-300 dark:border-amber-800' };
      default:
        return { label: 'System', color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700' };
    }
  };

  const domainInfo = getDomainBadge(clarification.domain);

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

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-200 dark:border-slate-800 max-w-2xl mx-auto my-6 animate-fadeIn">
      {/* Header with Domain Badge */}
      <div className="flex items-center justify-between gap-3 mb-4">
        <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${domainInfo.color}`}>
          {domainInfo.label}
        </span>
        <span className="text-xs text-slate-400 dark:text-slate-500 font-medium">
          Step 2: Disambiguation
        </span>
      </div>

      {/* Main Question */}
      <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white mb-2 leading-snug">
        {clarification.question}
      </h2>
      <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
        {clarification.prompt}
      </p>

      {/* Structured Option Cards */}
      <form onSubmit={handleSubmit}>
        <div className="space-y-3 mb-6">
          {clarification.options.map((option, idx) => {
            const isSelected = selectedOptionId === option.id && !isCustomMode;
            return (
              <div
                key={option.id}
                onClick={() => {
                  setSelectedOptionId(option.id);
                  setIsCustomMode(false);
                }}
                className={`group relative flex items-start gap-4 p-4 rounded-2xl border-2 transition-all cursor-pointer select-none ${
                  isSelected
                    ? 'border-blue-600 bg-blue-50/70 dark:bg-blue-950/40 dark:border-blue-500 shadow-sm'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-100/50 dark:hover:bg-slate-800/80'
                }`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                      isSelected
                        ? 'border-blue-600 dark:border-blue-500 bg-blue-600 dark:bg-blue-500'
                        : 'border-slate-300 dark:border-slate-600 group-hover:border-slate-400'
                    }`}
                  >
                    {isSelected && (
                      <div className="w-2 h-2 rounded-full bg-white" />
                    )}
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-semibold text-slate-900 dark:text-white">
                      {option.label}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500">
                      [{idx + 1}]
                    </span>
                  </div>
                  {option.description && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                      {option.description}
                    </p>
                  )}
                </div>
              </div>
            );
          })}

          {/* Custom Description Option */}
          <div
            onClick={() => setIsCustomMode(true)}
            className={`p-4 rounded-2xl border-2 transition-all cursor-pointer ${
              isCustomMode
                ? 'border-blue-600 bg-blue-50/70 dark:bg-blue-950/40 dark:border-blue-500'
                : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:border-slate-300 dark:hover:border-slate-700'
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <div
                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                  isCustomMode
                    ? 'border-blue-600 dark:border-blue-500 bg-blue-600 dark:bg-blue-500'
                    : 'border-slate-300 dark:border-slate-600'
                }`}
              >
                {isCustomMode && <div className="w-2 h-2 rounded-full bg-white" />}
              </div>
              <span className="text-sm font-semibold text-slate-900 dark:text-white">
                Describe in your own words
              </span>
            </div>
            {isCustomMode && (
              <textarea
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                placeholder="E.g. It happens right after opening Instagram and playing 4K videos..."
                className="w-full mt-2 p-3 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={2}
                autoFocus
              />
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
          >
            Back to Search
          </button>
          <button
            type="submit"
            disabled={isLoading || (!selectedOptionId && (!isCustomMode || !customText.trim()))}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-800 text-white font-semibold rounded-xl text-sm shadow-md transition-all flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Refining Diagnosis...
              </>
            ) : (
              'Confirm & Get Resolution →'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
