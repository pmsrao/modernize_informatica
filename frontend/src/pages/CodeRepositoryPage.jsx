import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';
import PageTabs from '../components/common/PageTabs.jsx';
import CodeRepoOverview from '../components/code/CodeRepoOverview.jsx';
import SyntaxHighlighter from '../components/common/SyntaxHighlighter.jsx';

/**
 * Code Repository Page
 * 
 * Displays a file tree view of generated code repository structure.
 * Shows the exact structure: review_summary.json, workflows/{workflow}/orchestration/{files}
 */
export default function CodeRepositoryPage() {
  const [repository, setRepository] = useState({});
  const [expanded, setExpanded] = useState(new Set());
  const [selectedFile, setSelectedFile] = useState(null);
  const [codeContent, setCodeContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingCode, setLoadingCode] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('Overview');

  useEffect(() => {
    loadRepository();
  }, []);

  useEffect(() => {
    if (selectedFile) {
      loadCodeContent(selectedFile);
    }
  }, [selectedFile]);

  const loadRepository = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.getCodeRepository();
      console.log('Repository API result:', result);
      if (result.success) {
        // Transform the repository structure to match expected format
        const transformed = transformRepositoryStructure(result.repository || {});
        console.log('Transformed repository:', transformed);
        setRepository(transformed);
        // Auto-expand first level directories
        const newExpanded = new Set();
        const firstLevelKeys = Object.keys(transformed).slice(0, 3); // Expand first 3 top-level items
        firstLevelKeys.forEach(key => {
          newExpanded.add(key);
        });
        console.log('Initial expanded set:', Array.from(newExpanded));
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

  const transformRepositoryStructure = (repo) => {
    // The API now returns a simple filesystem tree structure
    // Just return it as-is, no transformation needed
    if (!repo || typeof repo !== 'object') {
      return {};
    }
    
    return repo;
  };

  const loadCodeContent = async (filePath) => {
    if (!filePath) {
      setCodeContent('');
      return;
    }
    
    setLoadingCode(true);
    setError(null);
    try {
      console.log('Loading code content from:', filePath);
      // Convert absolute path to relative path if needed
      let relPath = filePath;
      if (filePath.includes('test_log/generated_ai')) {
        relPath = filePath.split('test_log/generated_ai/')[1] || filePath;
      } else if (filePath.includes('test_log/generated')) {
        relPath = filePath.split('test_log/generated/')[1] || filePath;
      }
      
      const result = await apiClient.getCodeFile(relPath);
      console.log('Code content result:', result);
      if (result.success) {
        setCodeContent(result.code || '');
      } else {
        setCodeContent(`// Error loading code: ${result.message || 'Unknown error'}\n// File path: ${relPath}`);
        setError(result.message || 'Failed to load code content');
      }
    } catch (err) {
      const errorMsg = `// Error loading code: ${err.message}\n// File path: ${filePath}`;
      setCodeContent(errorMsg);
      setError(err.message || 'Failed to load code content');
      console.error('Error loading code content:', err);
    } finally {
      setLoadingCode(false);
    }
  };

  const toggleExpand = (path) => {
    console.log('toggleExpand called with path:', path, 'Current expanded:', Array.from(expanded));
    setExpanded(prevExpanded => {
      const newExpanded = new Set(prevExpanded);
      if (newExpanded.has(path)) {
        newExpanded.delete(path);
        console.log('Collapsing:', path);
      } else {
        newExpanded.add(path);
        console.log('Expanding:', path);
      }
      console.log('New expanded set:', Array.from(newExpanded));
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
    
    Object.keys(tree).forEach(key => {
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
              {value.quality_score !== null && value.quality_score !== undefined && (
                <span style={{ 
                  padding: '2px 6px',
                  borderRadius: '3px',
                  background: value.quality_score >= 80 ? '#4CAF50' : 
                             value.quality_score >= 60 ? '#FF9800' : '#F44336',
                  color: 'white',
                  fontSize: '10px'
                }}>
                  {value.quality_score}
                </span>
              )}
            </div>
          </div>
        );
      } else if (typeof value === 'object' && !Array.isArray(value) && value !== null && (!value.type || value.type !== 'file')) {
        // It's a directory (not a file object with file_path)
        const isExpanded = expanded.has(currentPath);
        const isRoot = level === 0;
        const hasChildren = Object.keys(value).length > 0;
        
        console.log(`Rendering directory: ${currentPath}, hasChildren: ${hasChildren}, isExpanded: ${isExpanded}, children:`, Object.keys(value));
        
        items.push(
          <div key={currentPath} style={{ marginLeft: `${indent}px`, marginTop: '4px' }}>
            <div
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (hasChildren) {
                  console.log('Clicking folder:', currentPath, 'hasChildren:', hasChildren, 'isExpanded:', isExpanded);
                  toggleExpand(currentPath);
                }
              }}
              onMouseDown={(e) => {
                // Prevent text selection on folder click
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
        <div>Loading repository structure...</div>
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
        tabs={['Overview', 'Repository', 'Details']}
      />

      {/* Overview Tab */}
      {activeTab === 'Overview' && (
        <CodeRepoOverview onRefresh={loadRepository} />
      )}

      {/* Repository Tab */}
      {activeTab === 'Repository' && (
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
            background: '#f5f5f5',
            fontWeight: 'bold',
            fontSize: '14px'
          }}>
            Repository Structure
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '15px', fontFamily: 'monospace', fontSize: '12px' }}>
            {!hasData ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
                <div style={{ fontSize: '48px', marginBottom: '20px' }}>📁</div>
                <h3>No Code Files Found</h3>
                <p>No generated code files found in repository.</p>
                <p style={{ fontSize: '12px', marginTop: '10px', color: '#999' }}>
                  Run code generation to create code files.
                </p>
              </div>
            ) : (
              <div>
                {renderTree(repository)}
              </div>
            )}
          </div>
        </div>

        {/* Code Display */}
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
                {loadingCode ? (
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
                      <div>Loading code...</div>
                    </div>
                  </div>
                ) : (
                  <SyntaxHighlighter 
                    code={codeContent || '// No code content available'} 
                    filename={selectedFile}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      )}

      {/* Details Tab */}
      {activeTab === 'Details' && (
        <div style={{ 
          padding: '40px', 
          textAlign: 'center', 
          color: '#666',
          background: 'white',
          borderRadius: '8px',
          border: '1px solid #ddd',
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>📄</div>
          <h2 style={{ margin: '10px 0', color: '#333' }}>File Details</h2>
          <p style={{ margin: '5px 0', color: '#666' }}>
            Select a file from the Repository tab to view detailed information
          </p>
        </div>
      )}
    </div>
  );
}
