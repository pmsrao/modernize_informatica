import React, { useState, useMemo } from 'react';

/**
 * List View Component
 * 
 * Table-based list view as alternative to tree/grid view
 * - Shows: Name, Type, Complexity, Status, Actions
 * - Sortable columns
 * - Row selection
 */
export default function ModelListView({ 
  items = [],
  onItemClick,
  selectedItem = null,
  sortBy = 'name',
  sortOrder = 'asc'
}) {
  const [sortConfig, setSortConfig] = useState({ field: sortBy, order: sortOrder });

  const handleSort = (field) => {
    setSortConfig(prev => ({
      field,
      order: prev.field === field && prev.order === 'asc' ? 'desc' : 'asc'
    }));
  };

  const sortedItems = useMemo(() => {
    const sorted = [...items];
    
    sorted.sort((a, b) => {
      let aVal, bVal;
      
      if (sortConfig.field === 'name') {
        aVal = (a.name || a.transformation_name || '').toLowerCase();
        bVal = (b.name || b.transformation_name || '').toLowerCase();
      } else if (sortConfig.field === 'type') {
        aVal = (a.type || a.source_component_type || '').toLowerCase();
        bVal = (b.type || b.source_component_type || '').toLowerCase();
      } else if (sortConfig.field === 'complexity') {
        const complexityOrder = { 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'UNKNOWN': 0 };
        aVal = complexityOrder[a.complexity] || 0;
        bVal = complexityOrder[b.complexity] || 0;
      } else if (sortConfig.field === 'status') {
        aVal = (a.has_code ? 1 : 0);
        bVal = (b.has_code ? 1 : 0);
      } else {
        aVal = a[sortConfig.field] || '';
        bVal = b[sortConfig.field] || '';
      }
      
      if (aVal < bVal) return sortConfig.order === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.order === 'asc' ? 1 : -1;
      return 0;
    });
    
    return sorted;
  }, [items, sortConfig]);

  const complexityColors = {
    'LOW': '#4CAF50',
    'MEDIUM': '#FF9800',
    'HIGH': '#F44336',
    'UNKNOWN': '#9E9E9E'
  };

  const getSortIcon = (field) => {
    if (sortConfig.field !== field) return '⇅';
    return sortConfig.order === 'asc' ? '↑' : '↓';
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        background: 'white'
      }}>
        <thead>
          <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
            <th
              onClick={() => handleSort('name')}
              style={{
                padding: '12px',
                textAlign: 'left',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '13px',
                color: '#666',
                userSelect: 'none'
              }}
            >
              Name {getSortIcon('name')}
            </th>
            <th
              onClick={() => handleSort('type')}
              style={{
                padding: '12px',
                textAlign: 'left',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '13px',
                color: '#666',
                userSelect: 'none'
              }}
            >
              Type {getSortIcon('type')}
            </th>
            <th
              onClick={() => handleSort('complexity')}
              style={{
                padding: '12px',
                textAlign: 'left',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '13px',
                color: '#666',
                userSelect: 'none'
              }}
            >
              Complexity {getSortIcon('complexity')}
            </th>
            <th
              onClick={() => handleSort('status')}
              style={{
                padding: '12px',
                textAlign: 'left',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '13px',
                color: '#666',
                userSelect: 'none'
              }}
            >
              Status {getSortIcon('status')}
            </th>
            <th style={{
              padding: '12px',
              textAlign: 'left',
              fontWeight: '600',
              fontSize: '13px',
              color: '#666'
            }}>
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedItems.map((item, index) => {
            const isSelected = selectedItem && (
              selectedItem.name === item.name || 
              selectedItem.transformation_name === item.transformation_name
            );
            
            return (
              <tr
                key={item.name || item.transformation_name || index}
                onClick={() => onItemClick && onItemClick(item)}
                style={{
                  borderBottom: '1px solid #f0f0f0',
                  cursor: 'pointer',
                  background: isSelected ? '#E3F2FD' : 'white',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = '#f5f5f5';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = 'white';
                  }
                }}
              >
                <td style={{ padding: '12px', fontWeight: '500', fontSize: '14px' }}>
                  {item.name || item.transformation_name || 'Unknown'}
                </td>
                <td style={{ padding: '12px', fontSize: '13px', color: '#666' }}>
                  {item.type || item.source_component_type || 'N/A'}
                </td>
                <td style={{ padding: '12px' }}>
                  {item.complexity && item.complexity !== 'UNKNOWN' ? (
                    <span style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      background: complexityColors[item.complexity] || '#9E9E9E',
                      color: 'white',
                      fontSize: '11px',
                      fontWeight: 'bold'
                    }}>
                      {item.complexity}
                    </span>
                  ) : (
                    <span style={{ color: '#999', fontSize: '12px' }}>N/A</span>
                  )}
                </td>
                <td style={{ padding: '12px' }}>
                  {item.has_code ? (
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
                  ) : (
                    <span style={{ color: '#999', fontSize: '12px' }}>No Code</span>
                  )}
                </td>
                <td style={{ padding: '12px' }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onItemClick && onItemClick(item);
                    }}
                    style={{
                      padding: '6px 12px',
                      background: '#4A90E2',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    View
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      
      {sortedItems.length === 0 && (
        <div style={{ 
          padding: '40px', 
          textAlign: 'center', 
          color: '#666' 
        }}>
          No items to display
        </div>
      )}
    </div>
  );
}

