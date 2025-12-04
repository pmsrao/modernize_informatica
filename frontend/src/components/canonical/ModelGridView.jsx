import React, { useState, useMemo } from 'react';
import TransformationCard from './TransformationCard.jsx';

/**
 * Grid/Card View Component
 * 
 * Card-based layout as alternative to tree view
 * - Cards show: Name, Type, Complexity, Transformation count, Status
 * - Grouping options: By Pipeline, By Type, By Complexity
 * - Sort options: Name, Complexity, Transformation count
 */
export default function ModelGridView({ 
  items = [],
  onItemClick,
  selectedItem = null,
  groupBy = 'none', // 'none', 'pipeline', 'type', 'complexity'
  sortBy = 'name', // 'name', 'complexity', 'count'
  sortOrder = 'asc' // 'asc', 'desc'
}) {
  const [expandedGroups, setExpandedGroups] = useState(new Set());

  const toggleGroup = (groupKey) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupKey)) {
      newExpanded.delete(groupKey);
    } else {
      newExpanded.add(groupKey);
    }
    setExpandedGroups(newExpanded);
  };

  // Process items: group and sort
  const processedItems = useMemo(() => {
    let processed = [...items];

    // Sort items
    if (sortBy === 'name') {
      processed.sort((a, b) => {
        const nameA = (a.name || a.transformation_name || '').toLowerCase();
        const nameB = (b.name || b.transformation_name || '').toLowerCase();
        return sortOrder === 'asc' ? nameA.localeCompare(nameB) : nameB.localeCompare(nameA);
      });
    } else if (sortBy === 'complexity') {
      const complexityOrder = { 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'UNKNOWN': 0 };
      processed.sort((a, b) => {
        const orderA = complexityOrder[a.complexity] || 0;
        const orderB = complexityOrder[b.complexity] || 0;
        return sortOrder === 'asc' ? orderA - orderB : orderB - orderA;
      });
    } else if (sortBy === 'count') {
      processed.sort((a, b) => {
        const countA = a.transformation_count || a.task_count || 0;
        const countB = b.transformation_count || b.task_count || 0;
        return sortOrder === 'asc' ? countA - countB : countB - countA;
      });
    }

    // Group items
    if (groupBy === 'none') {
      return { 'All Items': processed };
    }

    const grouped = {};
    processed.forEach(item => {
      let groupKey = 'Other';
      
      if (groupBy === 'pipeline') {
        groupKey = item.pipeline_name || item.workflowName || 'Other';
      } else if (groupBy === 'type') {
        groupKey = item.type || item.source_component_type || 'Other';
      } else if (groupBy === 'complexity') {
        groupKey = item.complexity || 'UNKNOWN';
      }
      
      if (!grouped[groupKey]) {
        grouped[groupKey] = [];
      }
      grouped[groupKey].push(item);
    });

    return grouped;
  }, [items, groupBy, sortBy, sortOrder]);

  const isGroupExpanded = (groupKey) => expandedGroups.has(groupKey);

  return (
    <div style={{ padding: '10px' }}>
      {Object.entries(processedItems).map(([groupKey, groupItems]) => (
        <div key={groupKey} style={{ marginBottom: '20px' }}>
          {groupBy !== 'none' && (
            <div
              onClick={() => toggleGroup(groupKey)}
              style={{
                padding: '10px 15px',
                background: '#f5f5f5',
                border: '1px solid #ddd',
                borderRadius: '6px',
                marginBottom: '10px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              <span>
                {isGroupExpanded(groupKey) ? '▼' : '▶'} {groupKey} ({groupItems.length})
              </span>
            </div>
          )}
          
          {groupBy === 'none' || isGroupExpanded(groupKey) ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
              gap: '15px'
            }}>
              {groupItems.map((item, index) => {
                const itemType = item.source_component_type || 
                                (item.type === 'Pipeline' ? 'pipeline' : 
                                 item.type === 'Task' ? 'task' : 
                                 item.type === 'ReusableTransformation' ? 'reusable_transformation' : 
                                 'transformation');
                
                return (
                  <TransformationCard
                    key={item.name || item.transformation_name || index}
                    item={item}
                    type={itemType}
                    onClick={onItemClick}
                    selected={selectedItem && (
                      selectedItem.name === item.name || 
                      selectedItem.transformation_name === item.transformation_name
                    )}
                  />
                );
              })}
            </div>
          ) : null}
        </div>
      ))}
      
      {Object.keys(processedItems).length === 0 && (
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

