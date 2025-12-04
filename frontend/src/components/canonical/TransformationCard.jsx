import React from 'react';

/**
 * Transformation Card Component
 * 
 * Card component for grid view showing:
 * - Name, Type, Complexity
 * - Transformation count, Status
 * - Click handler for selection
 */
export default function TransformationCard({ 
  item, 
  type = 'transformation',
  onClick,
  selected = false 
}) {
  const complexity = item.complexity || 'UNKNOWN';
  const complexityColors = {
    'LOW': '#4CAF50',
    'MEDIUM': '#FF9800',
    'HIGH': '#F44336',
    'UNKNOWN': '#9E9E9E'
  };

  const typeIcons = {
    'pipeline': '📊',
    'task': '⚙️',
    'transformation': '🔄',
    'reusable_transformation': '🔁',
    'sub_pipeline': '📋'
  };

  const typeLabels = {
    'pipeline': 'Pipeline',
    'task': 'Task',
    'transformation': 'Transformation',
    'reusable_transformation': 'Reusable Transformation',
    'sub_pipeline': 'Sub Pipeline'
  };

  const hasCode = item.has_code || item.code_file_count > 0;
  const transformationCount = item.transformation_count || item.task_count || 0;

  return (
    <div
      onClick={() => onClick && onClick(item)}
      style={{
        border: selected ? '2px solid #4A90E2' : '1px solid #ddd',
        borderRadius: '8px',
        padding: '15px',
        background: selected ? '#E3F2FD' : 'white',
        cursor: 'pointer',
        transition: 'all 0.2s',
        boxShadow: selected ? '0 4px 8px rgba(74, 144, 226, 0.2)' : '0 2px 4px rgba(0,0,0,0.1)'
      }}
      onMouseEnter={(e) => {
        if (!selected) {
          e.currentTarget.style.borderColor = '#4A90E2';
          e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
        }
      }}
      onMouseLeave={(e) => {
        if (!selected) {
          e.currentTarget.style.borderColor = '#ddd';
          e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        }
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
        <span style={{ fontSize: '24px', marginRight: '10px' }}>
          {typeIcons[type] || '📄'}
        </span>
        <div style={{ flex: 1 }}>
          <div style={{ 
            fontWeight: 'bold', 
            fontSize: '14px', 
            color: '#333',
            marginBottom: '4px'
          }}>
            {item.name || item.transformation_name || 'Unknown'}
          </div>
          <div style={{ 
            fontSize: '12px', 
            color: '#666' 
          }}>
            {typeLabels[type] || type}
          </div>
        </div>
      </div>

      <div style={{ 
        display: 'flex', 
        gap: '8px', 
        flexWrap: 'wrap',
        marginTop: '10px'
      }}>
        {complexity && complexity !== 'UNKNOWN' && (
          <span style={{ 
            padding: '4px 8px',
            borderRadius: '4px',
            background: complexityColors[complexity] || '#9E9E9E',
            color: 'white',
            fontSize: '11px',
            fontWeight: 'bold'
          }}>
            {complexity}
          </span>
        )}
        
        {hasCode && (
          <span style={{ 
            padding: '4px 8px',
            borderRadius: '4px',
            background: '#4CAF50',
            color: 'white',
            fontSize: '11px',
            fontWeight: 'bold'
          }}>
            Has Code
          </span>
        )}

        {transformationCount > 0 && (
          <span style={{ 
            padding: '4px 8px',
            borderRadius: '4px',
            background: '#f0f0f0',
            color: '#666',
            fontSize: '11px'
          }}>
            {transformationCount} {type === 'pipeline' ? 'tasks' : 'transformations'}
          </span>
        )}
      </div>
    </div>
  );
}

