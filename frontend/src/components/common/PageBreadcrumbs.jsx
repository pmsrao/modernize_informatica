import React from 'react';

/**
 * Generic Breadcrumb Navigation Component
 * 
 * Reusable breadcrumb component for all pages
 */
export default function PageBreadcrumbs({ items = [], onNavigate }) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div style={{ 
      padding: '10px 15px', 
      background: '#f5f5f5', 
      borderRadius: '4px',
      fontSize: '14px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      marginBottom: '15px'
    }}>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && <span style={{ color: '#999' }}>›</span>}
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

