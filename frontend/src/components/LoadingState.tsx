import React, { useState, useEffect } from 'react';

interface LoadingStateProps {
  query: string;
}

const LOADING_STAGES = [
  'Understanding your description',
  'Finding relevant guidance',
  'Preparing your next step',
];

export const LoadingState: React.FC<LoadingStateProps> = ({ query }) => {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStage((prev) => (prev < LOADING_STAGES.length - 1 ? prev + 1 : prev));
    }, 1200);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="card loading-box view-transition">
      <div className="spinner" />
      <h3 className="loading-text">SmartGuide is checking this...</h3>
      <p className="loading-subtext">"{query}"</p>

      <div className="loading-stages">
        {LOADING_STAGES.map((stage, idx) => (
          <div
            key={stage}
            className={`loading-stage ${idx <= activeStage ? 'active' : ''} ${idx < activeStage ? 'done' : ''}`}
          >
            <div className="loading-stage-dot" />
            <span>{stage}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
