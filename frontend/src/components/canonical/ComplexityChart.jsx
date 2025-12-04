import React from 'react';

/**
 * Complexity Distribution Chart Component
 * 
 * Displays a simple bar chart showing complexity distribution
 * using CSS-based visualization (no external chart library required).
 */
export default function ComplexityChart({ data }) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        No complexity data available
      </div>
    );
  }

  const entries = Object.entries(data);
  const maxValue = Math.max(...entries.map(([_, count]) => count), 1);
  
  const complexityColors = {
    'LOW': '#4CAF50',
    'MEDIUM': '#FF9800',
    'HIGH': '#F44336',
    'UNKNOWN': '#9E9E9E'
  };

  return (
    <div style={{ padding: '10px 0' }}>
      {entries.map(([complexity, count]) => {
        const percentage = maxValue > 0 ? (count / maxValue) * 100 : 0;
        const color = complexityColors[complexity] || '#9E9E9E';
        
        return (
          <div key={complexity} style={{ marginBottom: '15px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              marginBottom: '5px',
              fontSize: '13px'
            }}>
              <span style={{ fontWeight: '500', color: '#333' }}>{complexity}</span>
              <span style={{ color: '#666' }}>{count}</span>
            </div>
            <div style={{
              width: '100%',
              height: '24px',
              background: '#f0f0f0',
              borderRadius: '4px',
              overflow: 'hidden',
              position: 'relative'
            }}>
              <div style={{
                width: `${percentage}%`,
                height: '100%',
                background: color,
                transition: 'width 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                paddingLeft: '8px',
                color: 'white',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {percentage > 10 ? `${Math.round(percentage)}%` : ''}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

