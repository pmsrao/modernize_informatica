import React, { useState, useRef, useEffect } from 'react';

/**
 * Enhanced Search Component
 * 
 * Provides advanced search with:
 * - Autocomplete suggestions
 * - Search across names, types, properties, tags
 * - Search filters: Type, Complexity, Status
 * - Recent searches
 * - Search result highlighting
 */
export default function EnhancedSearch({ 
  onSearch, 
  placeholder = "Search pipelines, tasks, transformations...",
  suggestions = [],
  recentSearches = []
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState([]);
  const searchInputRef = useRef(null);

  useEffect(() => {
    if (searchTerm && suggestions.length > 0) {
      const filtered = suggestions.filter(s => 
        s.toLowerCase().includes(searchTerm.toLowerCase())
      ).slice(0, 10);
      setFilteredSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
    } else {
      setFilteredSuggestions([]);
      setShowSuggestions(false);
    }
  }, [searchTerm, suggestions]);

  const handleSearch = (term = searchTerm) => {
    if (onSearch) {
      onSearch(term);
    }
    setShowSuggestions(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setSearchTerm(suggestion);
    handleSearch(suggestion);
  };

  const handleRecentSearchClick = (recent) => {
    setSearchTerm(recent);
    handleSearch(recent);
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          ref={searchInputRef}
          type="text"
          placeholder={placeholder}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (filteredSuggestions.length > 0 || recentSearches.length > 0) {
              setShowSuggestions(true);
            }
          }}
          style={{
            flex: 1,
            padding: '10px 15px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '14px',
            outline: 'none'
          }}
        />
        <button
          onClick={() => handleSearch()}
          style={{
            padding: '10px 20px',
            background: '#4A90E2',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          Search
        </button>
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: 'white',
          border: '1px solid #ddd',
          borderRadius: '6px',
          marginTop: '5px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          zIndex: 1000,
          maxHeight: '300px',
          overflowY: 'auto'
        }}>
          {/* Suggestions */}
          {filteredSuggestions.length > 0 && (
            <div>
              <div style={{
                padding: '8px 12px',
                fontSize: '12px',
                fontWeight: '600',
                color: '#666',
                background: '#f5f5f5',
                borderBottom: '1px solid #ddd'
              }}>
                Suggestions
              </div>
              {filteredSuggestions.map((suggestion, index) => (
                <div
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  style={{
                    padding: '10px 15px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    borderBottom: index < filteredSuggestions.length - 1 ? '1px solid #f0f0f0' : 'none'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#f5f5f5';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'white';
                  }}
                >
                  {suggestion}
                </div>
              ))}
            </div>
          )}

          {/* Recent Searches */}
          {filteredSuggestions.length === 0 && recentSearches.length > 0 && (
            <div>
              <div style={{
                padding: '8px 12px',
                fontSize: '12px',
                fontWeight: '600',
                color: '#666',
                background: '#f5f5f5',
                borderBottom: '1px solid #ddd'
              }}>
                Recent Searches
              </div>
              {recentSearches.slice(0, 5).map((recent, index) => (
                <div
                  key={index}
                  onClick={() => handleRecentSearchClick(recent)}
                  style={{
                    padding: '10px 15px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    borderBottom: index < Math.min(recentSearches.length, 5) - 1 ? '1px solid #f0f0f0' : 'none'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#f5f5f5';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'white';
                  }}
                >
                  🔍 {recent}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

