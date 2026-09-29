import React, { useState } from 'react';
import { Search, ArrowRight, X } from 'lucide-react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({ onSubmit, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  return (
    <div className="card view-transition">
      <div className="hero-section">
        <h1 className="hero-title">What's happening with your Galaxy device?</h1>
        <p className="hero-subtitle">
          Describe the problem in your own words.
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
            aria-label="Find a solution for your device problem"
          >
            <span>{isLoading ? 'Checking...' : 'Find a Solution'}</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </form>
    </div>
  );
};
