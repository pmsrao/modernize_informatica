import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';
import PageTabs from '../components/common/PageTabs.jsx';
import SourceRepoOverview from '../components/source/SourceRepoOverview.jsx';
import EnhancedSearch from '../components/common/EnhancedSearch.jsx';
import SyntaxHighlighter from '../components/common/SyntaxHighlighter.jsx';

/**
 * Source Repo View Page
 * 
 * Displays a file tree view of source repository structure (staging directory).
 * Shows the exact folder structure as it exists on disk.
 */
export default function SourceRepoViewPage() {
  const [repository, setRepository] = useState({});
  const [expanded, setExpanded] = useState(new Set());
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingFile, setLoadingFile] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('Overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState('all');

  useEffect(() => {
    loadRepository();
  }, []);

  useEffect(() => {
    if (selectedFile) {
      loadFileContent(selectedFile);
    }
  }, [selectedFile]);

  const loadRepository = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.getSourceRepository();
      console.log('Source repository API result:', result);
      if (result.success) {
        setRepository(result.repository || {});
        // Auto-expand first level directories
        const newExpanded = new Set();
        const firstLevelKeys = Object.keys(result.repository || {}).slice(0, 3);
        firstLevelKeys.forEach(key => {
          newExpanded.add(key);
        });
        setExpanded(newExpanded);
      } else {
        setError(result.message || 'Failed to load repository');
      }
    } catch (err) {
      setError(err.message || 'Failed to load repository');
      console.error('Error loading repository:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadFileContent = async (filePath) => {
    if (!filePath) {
      setFileContent('');
      return;
    }
    
    setLoadingFile(true);
    setError(null);
    try {
      const result = await apiClient.getSourceFile(filePath);
      console.log('File content result:', result);
      if (result.success) {
        if (result.is_binary) {
          setFileContent(`// Binary file (base64 encoded)\n// File size: ${result.file_size} bytes\n// Use a binary viewer to decode this content`);
        } else {
          setFileContent(result.content || '');
        }
      } else {
        setFileContent(`// Error loading file: ${result.message || 'Unknown error'}\n// File path: ${filePath}`);
        setError(result.message || 'Failed to load file content');
      }
    } catch (err) {
      const errorMsg = `// Error loading file: ${err.message}\n// File path: ${filePath}`;
      setFileContent(errorMsg);
      setError(err.message || 'Failed to load file content');
      console.error('Error loading file content:', err);
    } finally {
      setLoadingFile(false);
    }
  };

  const toggleExpand = (path) => {
    setExpanded(prevExpanded => {
      const newExpanded = new Set(prevExpanded);
      if (newExpanded.has(path)) {
        newExpanded.delete(path);
      } else {
        newExpanded.add(path);
      }
      return newExpanded;
    });
  };

  const getFileName = (filePath) => {
    if (!filePath) return 'Unknown';
    const parts = filePath.split('/');
    return parts[parts.length - 1];
  };

  const renderTree = (tree, path = '', level = 0) => {
    const items = [];
    const indent = level * 8;
    
    // Filter by search term and file type
    const filteredKeys = Object.keys(tree).filter(key => {
      // Search filter
      if (searchTerm && !key.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      
      // File type filter
      if (fileTypeFilter !== 'all') {
        const value = tree[key];
        if (typeof value === 'object' && value !== null && value.type === 'file') {
          const filePath = value.file_path || value.path || key;
          if (!filePath.toLowerCase().endsWith(fileTypeFilter.toLowerCase())) {
            return false;
          }
        } else if (typeof value === 'object' && value !== null) {
          // It's a directory, check if it contains matching files
          const hasMatchingFiles = Object.keys(value).some(subKey => {
            const subValue = value[subKey];
            if (typeof subValue === 'object' && subValue !== null && subValue.type === 'file') {
              const filePath = subValue.file_path || subValue.path || subKey;
              return filePath.toLowerCase().endsWith(fileTypeFilter.toLowerCase());
            }
            return false;
          });
          if (!hasMatchingFiles) {
            return false;
          }
        }
      }
      
      return true;
    });
    
    filteredKeys.forEach(key => {
      const currentPath = path ? `${path}/${key}` : key;
      const value = tree[key];
      
      if (typeof value === 'object' && !Array.isArray(value) && value !== null && value.type === 'file' && value.path) {
        // It's a file
        const filePath = value.file_path || value.path;
        const isSelected = selectedFile === filePath;
        items.push(
          <div key={currentPath} style={{ marginLeft: `${indent}px`, marginTop: '4px' }}>
            <div
              onClick={() => setSelectedFile(filePath)}
              style={{
                padding: '6px 8px',
                cursor: 'pointer',
                background: isSelected ? '#E3F2FD' : 'transparent',
                border: isSelected ? '2px solid #4A90E2' : '1px solid transparent',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '13px',
                fontFamily: 'monospace'
              }}
            >
              <span>📄</span>
              <span style={{ flex: 1 }}>{key}</span>
            </div>
          </div>
        );
      } else if (typeof value === 'object' && !Array.isArray(value) && value !== null && (!value.type || value.type !== 'file')) {
        // It's a directory
        const isExpanded = expanded.has(currentPath);
        const isRoot = level === 0;
        const hasChildren = Object.keys(value).length > 0;
        
        items.push(
          <div key={currentPath} style={{ marginLeft: `${indent}px`, marginTop: '4px' }}>
            <div
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (hasChildren) {
                  toggleExpand(currentPath);
                }
              }}
              onMouseDown={(e) => {
                if (hasChildren) {
                  e.preventDefault();
                }
              }}
              style={{
                padding: '6px 8px',
                cursor: hasChildren ? 'pointer' : 'default',
                background: isExpanded ? '#f5f5f5' : 'transparent',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '13px',
                fontFamily: isRoot ? 'monospace' : 'inherit',
                fontWeight: isRoot ? 'bold' : 'normal',
                userSelect: 'none',
                WebkitUserSelect: 'none',
                MozUserSelect: 'none',
                msUserSelect: 'none',
                minHeight: '28px',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (hasChildren) {
                  e.currentTarget.style.background = isExpanded ? '#e8e8e8' : '#f0f0f0';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = isExpanded ? '#f5f5f5' : 'transparent';
              }}
            >
              <span style={{ fontSize: '12px' }}>
                {hasChildren ? (isExpanded ? '📂' : '📁') : '📁'}
              </span>
              <span>{key}</span>
              {hasChildren && (
                <span style={{ fontSize: '10px', color: '#666', marginLeft: 'auto' }}>
                  ({Object.keys(value).length})
                </span>
              )}
            </div>
            {isExpanded && hasChildren && (
              <div style={{ marginLeft: '8px', marginTop: '4px' }}>
                {renderTree(value, currentPath, level + 1)}
              </div>
            )}
          </div>
        );
      }
    });
    
    return items;
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
        <div>Loading source repository...</div>
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

  const hasData = repository && Object.keys(repository).length > 0;

  return (
    <div style={{ 
      height: 'calc(100vh - 120px)', 
      display: 'flex', 
      flexDirection: 'column',
      padding: '20px',
      background: '#fafafa'
    }}>
      {/* Tabs */}
      <PageTabs 
        activeTab={activeTab} 
        onTabChange={setActiveTab}
        tabs={['Overview', 'Files', 'Details']}
      />

      {/* Main Content */}
      {activeTab === 'Overview' && (
        <SourceRepoOverview onRefresh={loadRepository} />
      )}

      {activeTab === 'Files' && (
        <div style={{ 
          display: 'flex', 
          gap: '20px', 
          flex: 1, 
          overflow: 'hidden',
          minHeight: 0
        }}>
        {/* Tree View */}
        <div style={{ 
          width: '450px', 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          overflow: 'hidden',
          background: 'white',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{ 
            padding: '15px', 
            borderBottom: '1px solid #ddd',
            background: '#f5f5f5'
          }}>
            <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '10px' }}>
              Source Repository Structure
            </div>
            <EnhancedSearch
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="Search files..."
            />
            <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', marginTop: '10px' }}>
              {['all', '.xml', '.json', '.txt'].map(type => (
                <button
                  key={type}
                  onClick={() => setFileTypeFilter(type)}
                  style={{
                    padding: '4px 8px',
                    background: fileTypeFilter === type ? '#4A90E2' : 'white',
                    color: fileTypeFilter === type ? 'white' : '#666',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '11px'
                  }}
                >
                  {type === 'all' ? 'All' : type}
                </button>
              ))}
            </div>
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '15px', fontFamily: 'monospace', fontSize: '12px' }}>
            {!hasData ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
                <div style={{ fontSize: '48px', marginBottom: '20px' }}>📁</div>
                <h3>No Source Files Found</h3>
                <p>No source files found in staging directory.</p>
                <p style={{ fontSize: '12px', marginTop: '10px', color: '#999' }}>
                  Files will appear here after running `make test-all`
                </p>
              </div>
            ) : (
              <div>
                {renderTree(repository)}
              </div>
            )}
          </div>
        </div>

        {/* File Display */}
        <div style={{ 
          flex: 1, 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          overflow: 'hidden',
          background: 'white',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {!selectedFile ? (
            <div style={{ 
              padding: '40px', 
              textAlign: 'center', 
              color: '#666',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>📄</div>
              <h2 style={{ margin: '10px 0', color: '#333' }}>Select a File</h2>
              <p style={{ margin: '5px 0', color: '#666' }}>
                Choose a file from the tree to view its contents
              </p>
            </div>
          ) : (
            <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
              <div style={{ 
                padding: '15px', 
                borderBottom: '1px solid #ddd',
                background: '#f5f5f5',
                fontSize: '13px',
                fontFamily: 'monospace'
              }}>
                <div><strong>File:</strong> {selectedFile}</div>
              </div>
              <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
                {loadingFile ? (
                  <div style={{ 
                    padding: '40px', 
                    textAlign: 'center',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div>
                      <div style={{ fontSize: '24px', marginBottom: '10px' }}>⏳</div>
                      <div>Loading file...</div>
                    </div>
                  </div>
                ) : (
                  <SyntaxHighlighter 
                    code={fileContent || '// No file content available'} 
                    filename={selectedFile}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      )}

      {activeTab === 'Details' && (
        <div style={{ 
          padding: '40px', 
          textAlign: 'center', 
          color: '#666',
          background: 'white',
          borderRadius: '8px',
          border: '1px solid #ddd'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>📄</div>
          <h2 style={{ margin: '10px 0', color: '#333' }}>File Details</h2>
          <p style={{ margin: '5px 0', color: '#666' }}>
            Select a file from the Files tab to view detailed information
          </p>
        </div>
      )}
    </div>
  );
}
