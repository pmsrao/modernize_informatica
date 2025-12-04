import React from 'react';

/**
 * Breadcrumb Navigation Component
 * 
 * Shows current navigation path: Pipeline > Task > Transformation
 * Uses generic canonical model terminology.
 */
export default function ModelBreadcrumbs({ items = [], onNavigate }) {
  if (!items || items.length === 0) {
    return (
      <div style={{ 
        padding: '10px 15px', 
        background: '#f5f5f5', 
        borderRadius: '4px',
        fontSize: '14px',
        color: '#666'
      }}>
        <span>Canonical Model</span>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: '10px 15px', 
      background: '#f5f5f5', 
      borderRadius: '4px',
      fontSize: '14px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    }}>
      <span 
        style={{ 
          color: '#666', 
          cursor: 'pointer',
          textDecoration: 'none'
        }}
        onClick={() => onNavigate && onNavigate(null)}
      >
        Canonical Model
      </span>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <span style={{ color: '#999' }}>›</span>
          {index < items.length - 1 ? (
            <span 
              style={{ 
                color: '#4A90E2', 
                cursor: 'pointer',
                textDecoration: 'none'
              }}
              onClick={() => onNavigate && onNavigate(item)}
            >
              {item.label || item.name}
            </span>
          ) : (
            <span style={{ color: '#333', fontWeight: '500' }}>
              {item.label || item.name}
            </span>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

