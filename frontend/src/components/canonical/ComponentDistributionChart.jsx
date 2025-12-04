import React from 'react';

/**
 * Component Distribution Chart Component
 * 
 * Displays a simple bar chart showing transformation type distribution
 * using CSS-based visualization (no external chart library required).
 */
export default function ComponentDistributionChart({ data }) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        No transformation type data available
      </div>
    );
  }

  const entries = Object.entries(data)
    .sort(([_, a], [__, b]) => b - a) // Sort by count descending
    .slice(0, 10); // Show top 10
  
  const maxValue = Math.max(...entries.map(([_, count]) => count), 1);
  
  // Generate colors for different types
  const colors = [
    '#4A90E2', '#4CAF50', '#FF9800', '#F44336', '#9C27B0',
    '#00BCD4', '#FFC107', '#795548', '#607D8B', '#E91E63'
  ];

  return (
    <div style={{ padding: '10px 0' }}>
      {entries.map(([type, count], index) => {
        const percentage = maxValue > 0 ? (count / maxValue) * 100 : 0;
        const color = colors[index % colors.length];
        
        return (
          <div key={type} style={{ marginBottom: '12px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              marginBottom: '5px',
              fontSize: '13px'
            }}>
              <span style={{ fontWeight: '500', color: '#333' }}>{type}</span>
              <span style={{ color: '#666' }}>{count}</span>
            </div>
            <div style={{
              width: '100%',
              height: '20px',
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
                fontSize: '11px',
                fontWeight: 'bold'
              }}>
                {percentage > 15 ? `${Math.round(percentage)}%` : ''}
              </div>
            </div>
          </div>
        );
      })}
      {Object.keys(data).length > 10 && (
        <div style={{ 
          marginTop: '10px', 
          fontSize: '12px', 
          color: '#999', 
          fontStyle: 'italic' 
        }}>
          Showing top 10 of {Object.keys(data).length} types
        </div>
      )}
    </div>
  );
}

