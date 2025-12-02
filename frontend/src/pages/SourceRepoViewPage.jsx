import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';

/**
 * Source Repo View Page
 * 
 * Lists all files made available to the accelerator (source repository view with file names).
 * Shows files from Neo4j with their metadata.
 */
export default function SourceRepoViewPage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.getAllComponents();
      if (result.success) {
        // Collect all files from components
        const allFiles = [];
        
        // Add workflow files
        (result.workflows || []).forEach(wf => {
          if (wf.file_metadata) {
            allFiles.push({
              ...wf.file_metadata,
              component_type: 'Workflow',
              component_name: wf.name
            });
          }
        });
        
        // Add session files
        (result.sessions || []).forEach(sess => {
          if (sess.file_metadata) {
            allFiles.push({
              ...sess.file_metadata,
              component_type: 'Session',
              component_name: sess.name
            });
          }
        });
        
        // Add worklet files
        (result.worklets || []).forEach(wl => {
          if (wl.file_metadata) {
            allFiles.push({
              ...wl.file_metadata,
              component_type: 'Worklet',
              component_name: wl.name
            });
          }
        });
        
        // Add mapping files
        (result.mappings || []).forEach(m => {
          if (m.file_metadata) {
            allFiles.push({
              ...m.file_metadata,
              component_type: 'Mapping',
              component_name: m.name
            });
          }
        });
        
        setFiles(allFiles);
      } else {
        setError(result.message || 'Failed to load files');
      }
    } catch (err) {
      setError(err.message || 'Failed to load files');
      console.error('Error loading files:', err);
    } finally {
      setLoading(false);
    }
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

  const getFileTypeColor = (type) => {
    const colors = {
      'workflow': '#50C878',
      'session': '#FFA500',
      'worklet': '#9B59B6',
      'mapping': '#4A90E2'
    };
    return colors[type.toLowerCase()] || '#95A5A6';
  };

  const getFileTypeIcon = (type) => {
    const icons = {
      'workflow': '🔄',
      'session': '⚙️',
      'worklet': '📦',
      'mapping': '📋'
    };
    return icons[type.toLowerCase()] || '📄';
  };

  const filteredFiles = filterType === 'all' 
    ? files 
    : files.filter(f => f.file_type?.toLowerCase() === filterType.toLowerCase());

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
        <div>Loading source files...</div>
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
    <div style={{ 
      height: 'calc(100vh - 120px)', 
      display: 'flex', 
      flexDirection: 'column',
      padding: '20px',
      background: '#fafafa'
    }}>
      {/* Header */}
      <div style={{ 
        marginBottom: '20px', 
        borderBottom: '2px solid #ddd', 
        paddingBottom: '20px' 
      }}>
        <h1 style={{ margin: 0, color: '#333' }}>Source Repo View</h1>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          Listing of files made available to this accelerator
        </p>
      </div>

      {/* Filter */}
      <div style={{ 
        marginBottom: '20px', 
        display: 'flex', 
        gap: '10px', 
        alignItems: 'center'
      }}>
        <label style={{ fontWeight: 'bold', fontSize: '14px' }}>Filter by Type:</label>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          style={{
            padding: '8px 16px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '14px',
            cursor: 'pointer',
            background: 'white'
          }}
        >
          <option value="all">All Types ({files.length})</option>
          <option value="workflow">Workflows ({files.filter(f => f.file_type?.toLowerCase() === 'workflow').length})</option>
          <option value="session">Sessions ({files.filter(f => f.file_type?.toLowerCase() === 'session').length})</option>
          <option value="worklet">Worklets ({files.filter(f => f.file_type?.toLowerCase() === 'worklet').length})</option>
          <option value="mapping">Mappings ({files.filter(f => f.file_type?.toLowerCase() === 'mapping').length})</option>
        </select>
      </div>

      {/* File List */}
      <div style={{ 
        flex: 1, 
        overflow: 'auto', 
        border: '1px solid #ddd', 
        borderRadius: '8px',
        background: 'white'
      }}>
        {filteredFiles.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>📭</div>
            <h3>No Files Found</h3>
            <p>Files will appear here after running `make test-all`</p>
          </div>
        ) : (
          <div style={{ padding: '15px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #ddd', background: '#f5f5f5' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Type</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Filename</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Component</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>File Path</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Size</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Parsed At</th>
                </tr>
              </thead>
              <tbody>
                {filteredFiles.map((file, idx) => (
                  <tr
                    key={idx}
                    onClick={() => setSelectedFile(file)}
                    style={{
                      borderBottom: '1px solid #eee',
                      cursor: 'pointer',
                      background: selectedFile?.file_path === file.file_path ? '#E3F2FD' : 'transparent',
                      transition: 'background 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      if (selectedFile?.file_path !== file.file_path) {
                        e.currentTarget.style.background = '#f5f5f5';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedFile?.file_path !== file.file_path) {
                        e.currentTarget.style.background = 'transparent';
                      }
                    }}
                  >
                    <td style={{ padding: '12px' }}>
                      <span style={{ 
                        padding: '4px 8px',
                        borderRadius: '4px',
                        background: getFileTypeColor(file.file_type),
                        color: 'white',
                        fontSize: '12px',
                        fontWeight: 'bold'
                      }}>
                        {getFileTypeIcon(file.file_type)} {file.file_type || 'Unknown'}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'monospace', fontSize: '13px' }}>
                      {file.filename || 'N/A'}
                    </td>
                    <td style={{ padding: '12px', fontSize: '13px' }}>
                      {file.component_name || 'N/A'}
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'monospace', fontSize: '12px', color: '#666', maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {file.file_path || 'N/A'}
                    </td>
                    <td style={{ padding: '12px', fontSize: '13px' }}>
                      {formatFileSize(file.file_size)}
                    </td>
                    <td style={{ padding: '12px', fontSize: '13px', color: '#666' }}>
                      {formatDate(file.parsed_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* File Detail Sidebar */}
      {selectedFile && (
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
            <h2 style={{ margin: 0, color: '#333', fontSize: '18px' }}>File Details</h2>
            <button
              onClick={() => setSelectedFile(null)}
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
            <strong>Filename:</strong>
            <div style={{ 
              fontFamily: 'monospace', 
              fontSize: '13px', 
              background: '#f5f5f5', 
              padding: '8px', 
              borderRadius: '4px',
              marginTop: '5px',
              wordBreak: 'break-all'
            }}>
              {selectedFile.filename}
            </div>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <strong>Component:</strong>
            <div style={{ fontSize: '13px', marginTop: '5px' }}>
              <span style={{ 
                padding: '4px 8px',
                borderRadius: '4px',
                background: getFileTypeColor(selectedFile.file_type),
                color: 'white',
                fontSize: '12px',
                fontWeight: 'bold',
                marginRight: '8px'
              }}>
                {selectedFile.component_type}
              </span>
              {selectedFile.component_name}
            </div>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <strong>File Path:</strong>
            <div style={{ 
              fontFamily: 'monospace', 
              fontSize: '12px', 
              background: '#f5f5f5', 
              padding: '8px', 
              borderRadius: '4px',
              marginTop: '5px',
              wordBreak: 'break-all'
            }}>
              {selectedFile.file_path}
            </div>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <strong>File Size:</strong>
            <div style={{ fontSize: '13px', marginTop: '5px' }}>
              {formatFileSize(selectedFile.file_size)}
            </div>
          </div>

          {selectedFile.parsed_at && (
            <div style={{ marginBottom: '15px' }}>
              <strong>Parsed At:</strong>
              <div style={{ fontSize: '13px', marginTop: '5px' }}>
                {formatDate(selectedFile.parsed_at)}
              </div>
            </div>
          )}

          {selectedFile.uploaded_at && (
            <div style={{ marginBottom: '15px' }}>
              <strong>Uploaded At:</strong>
              <div style={{ fontSize: '13px', marginTop: '5px' }}>
                {formatDate(selectedFile.uploaded_at)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

