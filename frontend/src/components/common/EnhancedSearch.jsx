import React from 'react';

/**
 * Generic Enhanced Search Component
 * 
 * Reusable search bar component for all pages
 */
export default function EnhancedSearch({ 
  value = '', 
  onChange, 
  placeholder = 'Search...',
  onClear 
}) {
  return (
    <div style={{
      position: 'relative',
      marginBottom: '15px'
    }}>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '10px 40px 10px 15px',
          border: '1px solid #ddd',
          borderRadius: '6px',
          fontSize: '14px',
          outline: 'none',
          transition: 'border-color 0.2s'
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = '#4A90E2';
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = '#ddd';
        }}
      />
      <div style={{
        position: 'absolute',
        right: '10px',
        top: '50%',
        transform: 'translateY(-50%)',
        display: 'flex',
        alignItems: 'center',
        gap: '5px'
      }}>
        {value && (
          <button
            onClick={() => {
              onChange && onChange('');
              onClear && onClear();
            }}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '18px',
              color: '#999',
              padding: '0',
              lineHeight: '1'
            }}
          >
            ×
          </button>
        )}
        <span style={{ fontSize: '16px', color: '#999' }}>🔍</span>
      </div>
    </div>
  );
}

