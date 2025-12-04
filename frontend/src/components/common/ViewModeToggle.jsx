import React from 'react';

/**
 * View Mode Toggle Component
 * 
 * Reusable component for switching between view modes (Tree, Grid, List, etc.)
 */
export default function ViewModeToggle({ 
  viewMode, 
  onViewModeChange, 
  modes = ['tree', 'grid', 'list'] 
}) {
  const modeLabels = {
    'tree': '🌳 Tree',
    'grid': '⊞ Grid',
    'list': '☰ List',
    'summary': '📊 Summary',
    'detailed': '📋 Detailed',
    'chart': '📈 Chart'
  };

  return (
    <div style={{
      display: 'flex',
      gap: '5px',
      background: '#f5f5f5',
      padding: '4px',
      borderRadius: '6px',
      border: '1px solid #ddd'
    }}>
      {modes.map((mode) => (
        <button
          key={mode}
          onClick={() => onViewModeChange && onViewModeChange(mode)}
          style={{
            padding: '6px 12px',
            background: viewMode === mode ? '#4A90E2' : 'transparent',
            color: viewMode === mode ? 'white' : '#666',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: viewMode === mode ? '600' : '400',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            if (viewMode !== mode) {
              e.currentTarget.style.background = '#e0e0e0';
            }
          }}
          onMouseLeave={(e) => {
            if (viewMode !== mode) {
              e.currentTarget.style.background = 'transparent';
            }
          }}
        >
          {modeLabels[mode] || mode}
        </button>
      ))}
    </div>
  );
}

