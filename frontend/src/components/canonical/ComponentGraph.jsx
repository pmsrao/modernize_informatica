import React from 'react';

/**
 * Component Relationship Graph Component
 * 
 * Interactive component relationship graph showing Pipeline → Task → Transformation connections
 * This is a placeholder implementation - can be enhanced with a graph visualization library
 * like React Flow (already in dependencies) or D3.js
 */
export default function ComponentGraph({ data = null }) {
  // Placeholder implementation
  // In a full implementation, this would use React Flow or D3.js to visualize
  // the component relationships as an interactive graph
  
  return (
    <div style={{ 
      padding: '40px', 
      textAlign: 'center', 
      color: '#666',
      background: 'white',
      border: '1px solid #ddd',
      borderRadius: '8px',
      minHeight: '400px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔗</div>
      <h3 style={{ margin: '10px 0', color: '#333' }}>Component Relationship Graph</h3>
      <p style={{ margin: '5px 0', color: '#666', maxWidth: '500px' }}>
        Interactive graph visualization showing relationships between Pipelines, Tasks, and Transformations.
        This can be enhanced with React Flow or D3.js for interactive exploration.
      </p>
      {data && (
        <div style={{ 
          marginTop: '20px', 
          padding: '15px', 
          background: '#f5f5f5', 
          borderRadius: '6px',
          fontSize: '12px',
          color: '#666'
        }}>
          Graph data available: {JSON.stringify(data).substring(0, 100)}...
        </div>
      )}
    </div>
  );
}

