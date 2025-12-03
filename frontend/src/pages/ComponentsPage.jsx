import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';

/**
 * Components Page - Shows all uploaded components from Neo4j
 * 
 * Displays workflows, sessions, worklets, and mappings with file metadata.
 * Replaces FileBrowserPage upload functionality with read-only visualization.
 */
export default function ComponentsPage() {
  const [components, setComponents] = useState({
    workflows: [],
    sessions: [],
    worklets: [],
    mappings: [],
    mapplets: []
  });
  const [counts, setCounts] = useState({
    workflows: 0,
    sessions: 0,
    worklets: 0,
    mappings: 0,
    mapplets: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState('all'); // 'all', 'workflow', 'session', 'worklet', 'mapping', 'mapplet'
  const [selectedComponent, setSelectedComponent] = useState(null);

  useEffect(() => {
    loadComponents();
  }, []);

  const loadComponents = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.getAllComponents();
      if (result.success) {
        setComponents({
          workflows: result.workflows || [],
          sessions: result.sessions || [],
          worklets: result.worklets || [],
          mappings: result.mappings || [],
          mapplets: result.mapplets || []
        });
        setCounts(result.counts || {
          workflows: 0,
          sessions: 0,
          worklets: 0,
          mappings: 0,
          mapplets: 0
        });
      } else {
        setError(result.message || 'Failed to load components');
      }
    } catch (err) {
      setError(err.message || 'Failed to load components');
      console.error('Error loading components:', err);
    } finally {
      setLoading(false);
    }
  };

  const getComponentTypeColor = (type) => {
    const colors = {
      'workflow': '#50C878',
      'session': '#FFA500',
      'worklet': '#9B59B6',
      'mapping': '#4A90E2',
      'mapplet': '#E74C3C'
    };
    return colors[type.toLowerCase()] || '#95A5A6';
  };

  const getComponentTypeIcon = (type) => {
    const icons = {
      'workflow': '🔄',
      'session': '⚙️',
      'worklet': '📦',
      'mapping': '📋',
      'mapplet': '🔧'
    };
    return icons[type.toLowerCase()] || '❓';
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  };

  const renderComponentCard = (component, type) => {
    const fileMeta = component.file_metadata || {};
    const color = getComponentTypeColor(type);
    const icon = getComponentTypeIcon(type);

    return (
      <div
        key={component.name}
        onClick={() => setSelectedComponent({ ...component, type })}
        style={{
          border: `2px solid ${selectedComponent?.name === component.name ? color : '#ddd'}`,
          borderRadius: '8px',
          padding: '15px',
          background: 'white',
          cursor: 'pointer',
          transition: 'all 0.2s',
          boxShadow: selectedComponent?.name === component.name 
            ? `0 4px 8px ${color}40` 
            : '0 2px 4px rgba(0,0,0,0.1)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
          <span style={{ fontSize: '24px', marginRight: '10px' }}>{icon}</span>
          <h3 style={{ margin: 0, color: '#333', fontSize: '16px' }}>{component.name}</h3>
        </div>
        
        {fileMeta.filename && (
          <div style={{ marginTop: '10px', fontSize: '13px', color: '#666' }}>
            <div><strong>File:</strong> {fileMeta.filename}</div>
            {fileMeta.file_size && (
              <div><strong>Size:</strong> {formatFileSize(fileMeta.file_size)}</div>
            )}
            {fileMeta.parsed_at && (
              <div><strong>Parsed:</strong> {formatDate(fileMeta.parsed_at)}</div>
            )}
          </div>
        )}
      </div>
    );
  };

  const filteredComponents = filterType === 'all' 
    ? {
        workflows: components.workflows,
        sessions: components.sessions,
        worklets: components.worklets,
        mappings: components.mappings,
        mapplets: components.mapplets
      }
    : {
        workflows: filterType === 'workflow' ? components.workflows : [],
        sessions: filterType === 'session' ? components.sessions : [],
        worklets: filterType === 'worklet' ? components.worklets : [],
        mappings: filterType === 'mapping' ? components.mappings : [],
        mapplets: filterType === 'mapplet' ? components.mapplets : []
      };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
        <div>Loading components...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <div style={{ 
          padding: '15px', 
          background: '#ffebee', 
          border: '1px solid #f44336', 
          borderRadius: '4px', 
          color: '#c62828' 
        }}>
          <strong>Error:</strong> {error}
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h1 style={{ margin: 0, color: '#333' }}>Component View</h1>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          All components loaded from Neo4j database
        </p>
      </div>

      {/* Summary Cards - Reduced Size */}
      <div style={{ 
        display: 'flex', 
        gap: '10px',
        marginBottom: '20px',
        flexWrap: 'wrap'
      }}>
        <div style={{ 
          background: 'white', 
          padding: '8px 16px', 
          borderRadius: '6px', 
          border: '1px solid #50C878',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ fontSize: '18px' }}>🔄</span>
          <div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#50C878' }}>{counts.workflows}</div>
            <div style={{ fontSize: '11px', color: '#666' }}>Workflows</div>
          </div>
        </div>
        <div style={{ 
          background: 'white', 
          padding: '8px 16px', 
          borderRadius: '6px', 
          border: '1px solid #FFA500',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ fontSize: '18px' }}>⚙️</span>
          <div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#FFA500' }}>{counts.sessions}</div>
            <div style={{ fontSize: '11px', color: '#666' }}>Sessions</div>
          </div>
        </div>
        <div style={{ 
          background: 'white', 
          padding: '8px 16px', 
          borderRadius: '6px', 
          border: '1px solid #9B59B6',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ fontSize: '18px' }}>📦</span>
          <div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#9B59B6' }}>{counts.worklets}</div>
            <div style={{ fontSize: '11px', color: '#666' }}>Worklets</div>
          </div>
        </div>
        <div style={{ 
          background: 'white', 
          padding: '8px 16px', 
          borderRadius: '6px', 
          border: '1px solid #4A90E2',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ fontSize: '18px' }}>📋</span>
          <div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#4A90E2' }}>{counts.mappings}</div>
            <div style={{ fontSize: '11px', color: '#666' }}>Mappings</div>
          </div>
        </div>
        <div style={{ 
          background: 'white', 
          padding: '8px 16px', 
          borderRadius: '6px', 
          border: '1px solid #E74C3C',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ fontSize: '18px' }}>🔧</span>
          <div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#E74C3C' }}>{counts.mapplets}</div>
            <div style={{ fontSize: '11px', color: '#666' }}>Mapplets</div>
          </div>
        </div>
      </div>

      {/* Filter Buttons */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        {['all', 'workflow', 'session', 'worklet', 'mapping', 'mapplet'].map(type => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            style={{
              padding: '8px 16px',
              background: filterType === type ? getComponentTypeColor(type) : '#f5f5f5',
              color: filterType === type ? 'white' : '#333',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: filterType === type ? 'bold' : 'normal'
            }}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
      </div>

      {/* Components Grid */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {(filterType === 'all' || filterType === 'workflow') && filteredComponents.workflows.length > 0 && (
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ marginBottom: '15px', color: '#333' }}>Workflows ({filteredComponents.workflows.length})</h2>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
              gap: '15px' 
            }}>
              {filteredComponents.workflows.map(wf => renderComponentCard(wf, 'workflow'))}
            </div>
          </div>
        )}

        {(filterType === 'all' || filterType === 'session') && filteredComponents.sessions.length > 0 && (
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ marginBottom: '15px', color: '#333' }}>Sessions ({filteredComponents.sessions.length})</h2>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
              gap: '15px' 
            }}>
              {filteredComponents.sessions.map(sess => renderComponentCard(sess, 'session'))}
            </div>
          </div>
        )}

        {(filterType === 'all' || filterType === 'worklet') && filteredComponents.worklets.length > 0 && (
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ marginBottom: '15px', color: '#333' }}>Worklets ({filteredComponents.worklets.length})</h2>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
              gap: '15px' 
            }}>
              {filteredComponents.worklets.map(wl => renderComponentCard(wl, 'worklet'))}
            </div>
          </div>
        )}

        {(filterType === 'all' || filterType === 'mapping') && filteredComponents.mappings.length > 0 && (
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ marginBottom: '15px', color: '#333' }}>Mappings ({filteredComponents.mappings.length})</h2>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
              gap: '15px' 
            }}>
              {filteredComponents.mappings.map(m => renderComponentCard(m, 'mapping'))}
            </div>
          </div>
        )}

        {(filterType === 'all' || filterType === 'mapplet') && filteredComponents.mapplets.length > 0 && (
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ marginBottom: '15px', color: '#333' }}>Mapplets ({filteredComponents.mapplets.length})</h2>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
              gap: '15px' 
            }}>
              {filteredComponents.mapplets.map(mpl => renderComponentCard(mpl, 'mapplet'))}
            </div>
          </div>
        )}

        {Object.values(filteredComponents).every(arr => arr.length === 0) && (
          <div style={{ padding: '60px', textAlign: 'center', color: '#999' }}>
            <div style={{ fontSize: '64px', marginBottom: '20px' }}>📭</div>
            <h3>No components found</h3>
            <p>Components will appear here after running `make test-all`</p>
          </div>
        )}
      </div>

      {/* Selected Component Detail Sidebar */}
      {selectedComponent && (
        <div style={{
          position: 'fixed',
          right: 0,
          top: 0,
          width: '400px',
          height: '100vh',
          background: 'white',
          boxShadow: '-2px 0 8px rgba(0,0,0,0.1)',
          padding: '20px',
          overflow: 'auto',
          zIndex: 1000
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2 style={{ margin: 0, color: '#333' }}>{selectedComponent.name}</h2>
            <button
              onClick={() => setSelectedComponent(null)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ×
            </button>
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <strong>Type:</strong> {selectedComponent.type}
          </div>

          {selectedComponent.file_metadata && (
            <div style={{ 
              background: '#f5f5f5', 
              padding: '15px', 
              borderRadius: '6px',
              marginBottom: '15px'
            }}>
              <h3 style={{ marginTop: 0, fontSize: '14px' }}>File Metadata</h3>
              <div style={{ fontSize: '13px' }}>
                <div><strong>Filename:</strong> {selectedComponent.file_metadata.filename || 'N/A'}</div>
                <div><strong>Path:</strong> {selectedComponent.file_metadata.file_path || 'N/A'}</div>
                {selectedComponent.file_metadata.file_size && (
                  <div><strong>Size:</strong> {formatFileSize(selectedComponent.file_metadata.file_size)}</div>
                )}
                {selectedComponent.file_metadata.parsed_at && (
                  <div><strong>Parsed:</strong> {formatDate(selectedComponent.file_metadata.parsed_at)}</div>
                )}
              </div>
            </div>
          )}

          {selectedComponent.properties && Object.keys(selectedComponent.properties).length > 0 && (
            <div>
              <h3 style={{ fontSize: '14px' }}>Properties</h3>
              <pre style={{ 
                background: '#f5f5f5', 
                padding: '10px', 
                borderRadius: '4px',
                fontSize: '12px',
                overflow: 'auto'
              }}>
                {JSON.stringify(selectedComponent.properties, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

