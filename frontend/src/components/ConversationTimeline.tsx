import React from 'react';
import type { TimelineEvent } from '../types/api';

interface ConversationTimelineProps {
  timeline: TimelineEvent[];
}

export const ConversationTimeline: React.FC<ConversationTimelineProps> = ({ timeline }) => {
  if (!timeline || timeline.length === 0) {
    return null;
  }

  const getStepIcon = (step: string, status: string) => {
    if (status === 'active') {
      return (
        <span className="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs animate-pulse font-bold">
          !
        </span>
      );
    }
    switch (step) {
      case 'query_received':
        return (
          <span className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 flex items-center justify-center text-xs font-semibold">
            1
          </span>
        );
      case 'clarification_requested':
        return (
          <span className="w-5 h-5 rounded-full bg-amber-100 dark:bg-amber-900/50 text-amber-600 dark:text-amber-400 flex items-center justify-center text-xs font-semibold">
            ?
          </span>
        );
      case 'clarification_answered':
        return (
          <span className="w-5 h-5 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-xs font-semibold">
            ✓
          </span>
        );
      case 'diagnosis_ready':
        return (
          <span className="w-5 h-5 rounded-full bg-green-500 text-white flex items-center justify-center text-xs font-bold">
            ✓
          </span>
        );
      default:
        return (
          <span className="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs">
            •
          </span>
        );
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 shadow-sm border border-slate-200 dark:border-slate-700/60 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-bold tracking-wider uppercase text-slate-400 dark:text-slate-400 flex items-center gap-1.5">
          <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Diagnostic Progression Timeline
        </h3>
        <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-700/60 px-2 py-0.5 rounded-full">
          {timeline.length} {timeline.length === 1 ? 'Step' : 'Steps'}
        </span>
      </div>

      <div className="relative pl-6 space-y-3 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-700">
        {timeline.map((event, idx) => (
          <div key={idx} className="relative flex items-start gap-3">
            <div className="absolute -left-6 top-0.5 bg-white dark:bg-slate-800 ring-4 ring-white dark:ring-slate-800 rounded-full">
              {getStepIcon(event.step, event.status)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                  {event.label}
                </span>
                {event.timestamp && (
                  <span className="text-[10px] text-slate-400">
                    {new Date(event.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                )}
              </div>
              {event.detail && (
                <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5 leading-relaxed">
                  {event.detail}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
