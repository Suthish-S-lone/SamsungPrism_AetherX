import React from 'react';
import { Activity, Check, HelpCircle, AlertCircle } from 'lucide-react';
import type { TimelineEvent } from '../types/api';

interface ConversationTimelineProps {
  timeline: TimelineEvent[];
}

export const ConversationTimeline: React.FC<ConversationTimelineProps> = ({ timeline }) => {
  if (!timeline || timeline.length === 0) {
    return null;
  }

  const renderStepNode = (step: string, status: string, idx: number) => {
    if (status === 'active') {
      return (
        <div className="timeline-node active" aria-label="Current active step">
          <AlertCircle size={12} color="#ffffff" />
        </div>
      );
    }
    if (status === 'completed') {
      return (
        <div className="timeline-node completed" aria-label="Completed step">
          <Check size={12} color="#00a86b" />
        </div>
      );
    }
    if (step === 'clarification_requested') {
      return (
        <div className="timeline-node" style={{ borderColor: 'var(--warning)', color: 'var(--warning)' }}>
          <HelpCircle size={12} />
        </div>
      );
    }
    return (
      <div className="timeline-node">
        {idx + 1}
      </div>
    );
  };

  return (
    <div className="timeline-card" role="region" aria-label="Diagnostic Progression Timeline">
      <div className="timeline-header">
        <div className="timeline-title">
          <Activity size={16} color="var(--primary)" />
          <span>Diagnostic Progression Timeline</span>
        </div>
        <span className="timeline-badge">
          {timeline.length} {timeline.length === 1 ? 'Step' : 'Steps'}
        </span>
      </div>

      <div className="timeline-list">
        {timeline.map((event, idx) => (
          <div key={idx} className="timeline-item">
            {renderStepNode(event.step, event.status, idx)}
            <div className="timeline-content">
              <div className="timeline-label-row">
                <span className="timeline-label">{event.label}</span>
                {event.timestamp && (
                  <span className="timeline-time">
                    {new Date(event.timestamp * 1000).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })}
                  </span>
                )}
              </div>
              {event.detail && (
                <p className="timeline-detail">
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
