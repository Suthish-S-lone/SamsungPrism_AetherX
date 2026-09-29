import React from 'react';
import { Smartphone, Battery, Thermometer, Eye, Camera, Cpu, ArrowRight, ChevronRight } from 'lucide-react';

interface LandingViewProps {
  onStartTroubleshooting: () => void;
  onQuickCategory: (query: string) => void;
  onTryExample: (query: string) => void;
}

interface CategoryCard {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
  description: string;
  query: string;
  colorClass: string;
}

const CATEGORIES: CategoryCard[] = [
  {
    icon: Battery,
    title: 'Battery & Charging',
    description: 'Battery drain, charging and power issues',
    query: 'My phone battery is draining really fast even when I barely use it.',
    colorClass: 'cat-battery',
  },
  {
    icon: Thermometer,
    title: 'Heating',
    description: 'Device temperature and thermal issues',
    query: 'My phone gets really hot',
    colorClass: 'cat-heating',
  },
  {
    icon: Eye,
    title: 'Display & Touch',
    description: 'Brightness, screen and touch issues',
    query: 'The screen brightness keeps changing on its own.',
    colorClass: 'cat-display',
  },
  {
    icon: Camera,
    title: 'Camera',
    description: 'Camera freezing, recording and image issues',
    query: 'The camera freezes whenever I try to record a video.',
    colorClass: 'cat-camera',
  },
  {
    icon: Cpu,
    title: 'Performance',
    description: 'Slowdowns, lag and responsiveness',
    query: 'My phone becomes extremely slow when I have many apps open.',
    colorClass: 'cat-performance',
  },
];

const EXAMPLES = [
  'My phone gets really hot',
  'My battery drains too quickly',
  'My screen brightness keeps changing',
  'My camera freezes when recording',
];

export const LandingView: React.FC<LandingViewProps> = ({
  onStartTroubleshooting,
  onQuickCategory,
  onTryExample,
}) => {
  return (
    <div className="landing-view">
      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-hero-icon">
          <Smartphone size={32} />
        </div>
        <h1 className="landing-hero-title">SmartGuide</h1>
        <p className="landing-hero-subtitle">
          Troubleshoot your Galaxy device with simple,
          <br />
          step-by-step guidance.
        </p>
        <button
          className="landing-cta"
          onClick={onStartTroubleshooting}
          aria-label="Start troubleshooting your device"
        >
          <span>Start Troubleshooting</span>
          <ArrowRight size={20} />
        </button>
      </section>

      {/* Category Cards */}
      <section className="landing-categories">
        <h2 className="landing-section-title">What can we help with?</h2>
        <div className="landing-category-grid">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            return (
              <button
                key={cat.title}
                type="button"
                className={`landing-category-card ${cat.colorClass}`}
                onClick={() => onQuickCategory(cat.query)}
                aria-label={`Get help with ${cat.title}`}
              >
                <div className="landing-cat-icon-wrap">
                  <Icon size={22} />
                </div>
                <div className="landing-cat-text">
                  <span className="landing-cat-title">{cat.title}</span>
                  <span className="landing-cat-desc">{cat.description}</span>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Try an Example */}
      <section className="landing-examples">
        <h2 className="landing-section-title">Try an example</h2>
        <div className="landing-example-list">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              className="landing-example-item"
              onClick={() => onTryExample(example)}
              aria-label={`Try example: ${example}`}
            >
              <span className="landing-example-text">"{example}"</span>
              <ChevronRight size={18} className="landing-example-arrow" />
            </button>
          ))}
        </div>
      </section>

      {/* Prototype Disclaimer */}
      <footer className="landing-footer">
        <span>Samsung PRISM Theme 2 Prototype</span>
      </footer>
    </div>
  );
};
