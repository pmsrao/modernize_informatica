import React from 'react';

/**
 * Tab Navigation Component
 * 
 * Provides tab-based navigation for different views:
 * - Overview: Dashboard with statistics and charts
 * - Components: Tree/grid view of all components
 * - Lineage: Data flow visualization
 * - Details: Current detail view
 */
export default function ModelTabs({ activeTab, onTabChange, tabs = ['Overview', 'Components', 'Lineage', 'Details'] }) {
  return (
    <div style={{
      borderBottom: '2px solid #ddd',
      marginBottom: '20px'
    }}>
      <div style={{
        display: 'flex',
        gap: '0'
      }}>
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => onTabChange && onTabChange(tab)}
            style={{
              padding: '12px 24px',
              background: activeTab === tab ? 'white' : 'transparent',
              border: 'none',
              borderBottom: activeTab === tab ? '3px solid #4A90E2' : '3px solid transparent',
              color: activeTab === tab ? '#4A90E2' : '#666',
              fontWeight: activeTab === tab ? '600' : '400',
              cursor: 'pointer',
              fontSize: '14px',
              transition: 'all 0.2s',
              position: 'relative',
              top: '2px'
            }}
            onMouseEnter={(e) => {
              if (activeTab !== tab) {
                e.currentTarget.style.color = '#4A90E2';
                e.currentTarget.style.background = '#f5f5f5';
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== tab) {
                e.currentTarget.style.color = '#666';
                e.currentTarget.style.background = 'transparent';
              }
            }}
          >
            {tab}
          </button>
        ))}
      </div>
    </div>
  );
}

