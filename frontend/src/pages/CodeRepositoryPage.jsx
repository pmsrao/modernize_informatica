import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';

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
        // Auto-expand workflows directory and first workflow
        const newExpanded = new Set(['workflows']);
        if (transformed.workflows && Object.keys(transformed.workflows).length > 0) {
          const firstWorkflow = Object.keys(transformed.workflows)[0];
          newExpanded.add(`workflows/${firstWorkflow}`);
          if (transformed.workflows[firstWorkflow]?.orchestration) {
            newExpanded.add(`workflows/${firstWorkflow}/orchestration`);
          }
        }
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
    // Transform from workflow/session/mapping/code_files to workflows/{workflow}/orchestration/{files}
    const transformed = {
      'review_summary.json': { type: 'file', path: 'review_summary.json' },
      'workflows': {}
    };

    // Handle empty or invalid repo
    if (!repo || typeof repo !== 'object') {
      return transformed;
    }

    // Helper function to extract workflow name from file path
    const extractWorkflowFromPath = (filePath) => {
      if (!filePath) return null;
      // Look for pattern: .../workflows/{workflow_name}/...
      const parts = filePath.split('/');
      const workflowsIndex = parts.findIndex(p => p === 'workflows');
      if (workflowsIndex >= 0 && workflowsIndex < parts.length - 1) {
        return parts[workflowsIndex + 1];
      }
      return null;
    };

    Object.keys(repo).forEach(workflowName => {
      const workflow = repo[workflowName];
      if (!workflow || typeof workflow !== 'object') return;
      
      // For "standalone", try to extract workflow name from file paths
      let actualWorkflowName = workflowName;
      if (workflowName === 'standalone') {
        // Try to find workflow name from any file path
        let foundWorkflow = null;
        Object.keys(workflow).forEach(sessionName => {
          const session = workflow[sessionName];
          if (!session || typeof session !== 'object') return;
          Object.keys(session).forEach(mappingName => {
            const mapping = session[mappingName];
            if (Array.isArray(mapping)) {
              mapping.forEach(codeFile => {
                if (codeFile?.file_path) {
                  const extracted = extractWorkflowFromPath(codeFile.file_path);
                  if (extracted) {
                    foundWorkflow = extracted;
                  }
                }
              });
            }
          });
        });
        if (foundWorkflow) {
          actualWorkflowName = foundWorkflow;
        } else {
          // If we can't extract, use "standalone" but don't skip it
          actualWorkflowName = 'standalone';
        }
      }
      
      // Normalize workflow name (remove wf_ prefix, convert to lowercase)
      const normalizedWorkflowName = actualWorkflowName.toLowerCase().replace(/^wf_/, '');
      
      if (!transformed.workflows[normalizedWorkflowName]) {
        transformed.workflows[normalizedWorkflowName] = {
          'orchestration': {}
        };
      }
      
      const workflowDir = transformed.workflows[normalizedWorkflowName];

      // Collect all code files from sessions/mappings
      Object.keys(workflow).forEach(sessionName => {
        const session = workflow[sessionName];
        if (!session || typeof session !== 'object') return;
        
        Object.keys(session).forEach(mappingName => {
          const mapping = session[mappingName];
          if (Array.isArray(mapping)) {
            mapping.forEach(codeFile => {
              if (!codeFile || typeof codeFile !== 'object') return;
              
              // Get file name from file_path
              const filePath = codeFile.file_path;
              if (!filePath) return;
              
              const fileName = filePath.split('/').pop();
              if (!fileName) return;
              
              // Store the code file with its full path
              if (!workflowDir.orchestration[fileName]) {
                workflowDir.orchestration[fileName] = {
                  ...codeFile,
                  file_path: filePath
                };
              }
            });
          }
        });
      });
    });

    return transformed;
  };

  const loadCodeContent = async (filePath) => {
    setLoadingCode(true);
    try {
      // Handle special case for review_summary.json - it might not exist as a code file
      if (filePath === 'review_summary.json') {
        // Try to find it in the generated code directory
        // For now, just show a message
        setCodeContent('// review_summary.json - This file is generated during code review process\n// It contains summary of code quality checks and recommendations');
        return;
      }
      
      const result = await apiClient.getCodeFile(filePath);
      if (result.success) {
        setCodeContent(result.code || '');
      } else {
        setCodeContent(`// Error loading code: ${result.message}\n// File path: ${filePath}`);
      }
    } catch (err) {
      setCodeContent(`// Error loading code: ${err.message}\n// File path: ${filePath}`);
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
    const indent = level * 20;
    
    Object.keys(tree).forEach(key => {
      const currentPath = path ? `${path}/${key}` : key;
      const value = tree[key];
      
      if (key === 'review_summary.json') {
        // Root level file - check if it has a file_path property
        const filePath = value?.file_path || value?.path || 'review_summary.json';
        items.push(
          <div key={currentPath} style={{ marginLeft: `${indent}px`, marginTop: '4px' }}>
            <div
              onClick={() => setSelectedFile(filePath)}
              style={{
                padding: '6px 8px',
                cursor: 'pointer',
                background: selectedFile === filePath ? '#E3F2FD' : 'transparent',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '13px',
                fontFamily: 'monospace'
              }}
            >
              <span>📄</span>
              <span>{key}</span>
            </div>
          </div>
        );
      } else if (typeof value === 'object' && !Array.isArray(value) && value !== null && !value.file_path) {
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
              <div style={{ marginLeft: '20px', marginTop: '4px' }}>
                {renderTree(value, currentPath, level + 1)}
              </div>
            )}
          </div>
        );
      } else if (value && typeof value === 'object' && value.file_path) {
        // It's a code file
        const filePath = value.file_path;
        const fileName = getFileName(filePath);
        const isSelected = selectedFile === filePath;
        
        items.push(
          <div key={currentPath} style={{ marginLeft: `${indent}px`, marginTop: '4px' }}>
            <div
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(filePath);
              }}
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
              <span style={{ flex: 1 }}>{fileName}</span>
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

  const workflows = Object.keys(repository.workflows || {});
  const hasData = workflows.length > 0 || repository['review_summary.json'];

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
        <h1 style={{ margin: 0, color: '#333' }}>Code Repository</h1>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          File tree view of generated code repository structure
        </p>
      </div>

      {/* Main Content */}
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
                  <pre style={{ 
                    margin: 0,
                    padding: '15px',
                    background: '#fafafa',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    overflow: 'auto',
                    fontSize: '13px',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre',
                    lineHeight: '1.5'
                  }}>
                    <code>{codeContent || '// No code content available'}</code>
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
