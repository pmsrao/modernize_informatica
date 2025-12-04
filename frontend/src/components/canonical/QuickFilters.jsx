import React from 'react';

/**
 * Quick Filter Bar Component
 * 
 * Provides quick filter buttons for:
 * - Complexity: All, High, Medium, Low
 * - Type: Pipelines, Tasks, Transformations, Reusable Transformations
 * - Status: With Code, Without Code, Validated, Needs Review
 */
export default function QuickFilters({ 
  activeFilters = {}, 
  onFilterChange 
}) {
  const complexityFilters = [
    { key: 'all', label: 'All Complexity' },
    { key: 'LOW', label: 'Low' },
    { key: 'MEDIUM', label: 'Medium' },
    { key: 'HIGH', label: 'High' }
  ];

  const typeFilters = [
    { key: 'all', label: 'All Types' },
    { key: 'pipeline', label: 'Pipelines' },
    { key: 'task', label: 'Tasks' },
    { key: 'transformation', label: 'Transformations' },
    { key: 'reusable_transformation', label: 'Reusable' }
  ];

  const statusFilters = [
    { key: 'all', label: 'All Status' },
    { key: 'with_code', label: 'With Code' },
    { key: 'without_code', label: 'Without Code' },
    { key: 'needs_review', label: 'Needs Review' }
  ];

  const handleFilterClick = (category, key) => {
    if (onFilterChange) {
      const newFilters = { ...activeFilters };
      if (key === 'all') {
        delete newFilters[category];
      } else {
        newFilters[category] = key;
      }
      onFilterChange(newFilters);
    }
  };

  const isActive = (category, key) => {
    if (key === 'all') {
      return !activeFilters[category];
    }
    return activeFilters[category] === key;
  };

  return (
    <div style={{
      padding: '15px',
      background: '#f9f9f9',
      borderRadius: '6px',
      marginBottom: '20px',
      border: '1px solid #ddd'
    }}>
      <div style={{ marginBottom: '15px' }}>
        <div style={{ 
          fontSize: '12px', 
          fontWeight: '600', 
          color: '#666', 
          marginBottom: '8px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Complexity
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {complexityFilters.map(filter => (
            <button
              key={filter.key}
              onClick={() => handleFilterClick('complexity', filter.key)}
              style={{
                padding: '6px 12px',
                background: isActive('complexity', filter.key) ? '#4A90E2' : 'white',
                color: isActive('complexity', filter.key) ? 'white' : '#666',
                border: '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: isActive('complexity', filter.key) ? '600' : '400',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!isActive('complexity', filter.key)) {
                  e.currentTarget.style.borderColor = '#4A90E2';
                  e.currentTarget.style.color = '#4A90E2';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive('complexity', filter.key)) {
                  e.currentTarget.style.borderColor = '#ddd';
                  e.currentTarget.style.color = '#666';
                }
              }}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: '15px' }}>
        <div style={{ 
          fontSize: '12px', 
          fontWeight: '600', 
          color: '#666', 
          marginBottom: '8px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Type
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {typeFilters.map(filter => (
            <button
              key={filter.key}
              onClick={() => handleFilterClick('type', filter.key)}
              style={{
                padding: '6px 12px',
                background: isActive('type', filter.key) ? '#4A90E2' : 'white',
                color: isActive('type', filter.key) ? 'white' : '#666',
                border: '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: isActive('type', filter.key) ? '600' : '400',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!isActive('type', filter.key)) {
                  e.currentTarget.style.borderColor = '#4A90E2';
                  e.currentTarget.style.color = '#4A90E2';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive('type', filter.key)) {
                  e.currentTarget.style.borderColor = '#ddd';
                  e.currentTarget.style.color = '#666';
                }
              }}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div style={{ 
          fontSize: '12px', 
          fontWeight: '600', 
          color: '#666', 
          marginBottom: '8px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Status
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {statusFilters.map(filter => (
            <button
              key={filter.key}
              onClick={() => handleFilterClick('status', filter.key)}
              style={{
                padding: '6px 12px',
                background: isActive('status', filter.key) ? '#4A90E2' : 'white',
                color: isActive('status', filter.key) ? 'white' : '#666',
                border: '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: isActive('status', filter.key) ? '600' : '400',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!isActive('status', filter.key)) {
                  e.currentTarget.style.borderColor = '#4A90E2';
                  e.currentTarget.style.color = '#4A90E2';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive('status', filter.key)) {
                  e.currentTarget.style.borderColor = '#ddd';
                  e.currentTarget.style.color = '#666';
                }
              }}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

