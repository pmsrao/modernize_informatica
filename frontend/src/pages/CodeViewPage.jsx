import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';

/**
 * Code View Page
 * 
 * Displays generated code organized by workflow → session → mapping → code files.
 * Shows workflow-based file structure with file names.
 */
export default function CodeViewPage() {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [selectedMapping, setSelectedMapping] = useState(null);
  const [codeFiles, setCodeFiles] = useState([]);
  const [selectedCodeFile, setSelectedCodeFile] = useState(null);
  const [codeContent, setCodeContent] = useState('');
  const [workflowStructure, setWorkflowStructure] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingCode, setLoadingCode] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  useEffect(() => {
    if (selectedWorkflow) {
      loadWorkflowStructure(selectedWorkflow);
    }
  }, [selectedWorkflow]);

  useEffect(() => {
    if (selectedMapping) {
      loadCodeFiles(selectedMapping);
    }
  }, [selectedMapping]);

  useEffect(() => {
    if (selectedCodeFile) {
      loadCodeContent(selectedCodeFile.file_path);
    }
  }, [selectedCodeFile]);

  const loadWorkflows = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.listWorkflows();
      if (result.success) {
        setWorkflows(result.workflows || []);
        if (result.workflows && result.workflows.length > 0) {
          setSelectedWorkflow(result.workflows[0].name);
        }
      } else {
        setError(result.message || 'Failed to load workflows');
      }
    } catch (err) {
      setError(err.message || 'Failed to load workflows');
      console.error('Error loading workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadWorkflowStructure = async (workflowName) => {
    setLoadingCode(true);
    setError(null);
    try {
      const result = await apiClient.getWorkflowStructure(workflowName);
      console.log('Workflow structure result:', result);
      if (result.success) {
        // API returns { success: true, workflow: {...} }
        const workflow = result.workflow || result;
        console.log('Workflow structure:', workflow);
        console.log('Tasks/Sessions:', workflow.tasks || workflow.sessions);
        
        // Log transformation details for debugging
        const tasks = workflow.tasks || workflow.sessions || [];
        tasks.forEach((task, idx) => {
          const transformations = task.transformations || task.mappings || [];
          console.log(`Task ${idx} (${task.name}): ${transformations.length} transformation(s)`, transformations);
        });
        
        setWorkflowStructure(workflow);
        setSelectedSession(null);
        setSelectedMapping(null);
        setCodeFiles([]);
        setSelectedCodeFile(null);
        setCodeContent('');
      } else {
        setError(result.message || 'Failed to load workflow structure');
        setWorkflowStructure(null);
      }
    } catch (err) {
      console.error('Error loading workflow structure:', err);
      setError(err.message || 'Failed to load workflow structure');
      setWorkflowStructure(null);
    } finally {
      setLoadingCode(false);
    }
  };

  const loadCodeFiles = async (mappingName) => {
    setLoadingCode(true);
    setError(null);
    try {
      const result = await apiClient.getMappingCode(mappingName);
      console.log('Code files result for', mappingName, ':', result);
      if (result.success) {
        const files = result.code_files || [];
        console.log('Found', files.length, 'code file(s)');
        setCodeFiles(files);
        if (files.length > 0) {
          setSelectedCodeFile(files[0]);
        } else {
          setSelectedCodeFile(null);
          setCodeContent('');
          // Show helpful message if no files found
          console.warn(`No code files found for mapping: ${mappingName}`);
        }
      } else {
        setError(result.message || 'Failed to load code files');
        setCodeFiles([]);
        setSelectedCodeFile(null);
      }
    } catch (err) {
      console.error('Error loading code files:', err);
      setError(err.message || 'Failed to load code files');
      setCodeFiles([]);
      setSelectedCodeFile(null);
    } finally {
      setLoadingCode(false);
    }
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
      const result = await apiClient.getCodeFile(filePath);
      console.log('Code content result:', result);
      if (result.success) {
        setCodeContent(result.code || '');
      } else {
        const errorMsg = `// Error loading code: ${result.message || 'Unknown error'}\n// File path: ${filePath}`;
        setCodeContent(errorMsg);
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

  const handleWorkflowSelect = (workflowName) => {
    setSelectedWorkflow(workflowName);
    setSelectedSession(null);
    setSelectedMapping(null);
    setCodeFiles([]);
    setSelectedCodeFile(null);
    setCodeContent('');
  };

  const handleSessionSelect = (session) => {
    setSelectedSession(session);
    setSelectedMapping(null);
    setCodeFiles([]);
    setSelectedCodeFile(null);
    setCodeContent('');
    
    // Check if session has transformations
    const transformations = session.transformations || session.mappings || [];
    if (transformations.length === 0) {
      // Show message that this session has no mappings
      setCodeContent(`// This session (${session.name}) has no associated transformations/mappings.\n// Sessions without mappings typically represent control tasks (e.g., email notifications, command tasks, decision points).\n// No code generation is needed for these tasks.`);
    }
  };

  const handleMappingSelect = (mapping) => {
    const mappingName = mapping.mapping_name || mapping.name || mapping.transformation_name;
    console.log('Mapping selected:', mappingName, 'from mapping object:', mapping);
    if (!mappingName) {
      console.error('No mapping name found in mapping object:', mapping);
      setError('Invalid mapping: no name found');
      return;
    }
    setSelectedMapping(mappingName);
    setCodeFiles([]);
    setSelectedCodeFile(null);
    setCodeContent('');
  };

  const handleCodeFileSelect = (file) => {
    setSelectedCodeFile(file);
  };

  const getFileName = (filePath) => {
    if (!filePath) return 'Unknown';
    const parts = filePath.split('/');
    return parts[parts.length - 1];
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
        <div>Loading workflows...</div>
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

  // Support both generic terminology (tasks) and Informatica terminology (sessions)
  const sessions = workflowStructure?.tasks || workflowStructure?.sessions || [];

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
        <h1 style={{ margin: 0, color: '#333' }}>Code View</h1>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          View generated code organized by workflow → task → transformation → code files
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
        {/* Workflow/Session/Mapping Tree */}
        <div style={{ 
          width: '350px', 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          overflow: 'hidden',
          background: 'white',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {/* Workflow Selection */}
          <div style={{ 
            padding: '15px', 
            borderBottom: '1px solid #ddd',
            background: '#f5f5f5'
          }}>
            <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '8px' }}>
              Workflow:
            </label>
            <select
              value={selectedWorkflow || ''}
              onChange={(e) => handleWorkflowSelect(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              {workflows.map(wf => (
                <option key={wf.name} value={wf.name}>{wf.name}</option>
              ))}
            </select>
          </div>

          {/* Tasks and Transformations */}
          <div style={{ flex: 1, overflow: 'auto', padding: '10px' }}>
            {!selectedWorkflow ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                Select a workflow
              </div>
            ) : loadingCode ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                <div style={{ fontSize: '24px', marginBottom: '10px' }}>⏳</div>
                <div>Loading workflow structure...</div>
              </div>
            ) : error ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#c62828' }}>
                <div>Error: {error}</div>
              </div>
            ) : !workflowStructure ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                Failed to load workflow structure
              </div>
            ) : sessions.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                <div style={{ fontSize: '32px', marginBottom: '10px' }}>📭</div>
                <div>No tasks found in this workflow</div>
                <div style={{ fontSize: '12px', marginTop: '5px', color: '#999' }}>
                  This workflow may not have any tasks configured
                </div>
              </div>
            ) : (
              sessions.map((session, idx) => {
                const isSessionSelected = selectedSession?.name === session.name;
                // API returns 'transformations', but support both for backward compatibility
                const transformations = session.transformations || session.mappings || [];
                return (
                  <div key={session.name || idx} style={{ marginBottom: '10px' }}>
                    <div
                      onClick={() => handleSessionSelect(session)}
                      style={{
                        padding: '10px',
                        background: isSessionSelected ? '#E3F2FD' : '#f5f5f5',
                        border: isSessionSelected ? '2px solid #4A90E2' : '1px solid #ddd',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        marginBottom: '5px',
                        fontWeight: 'bold',
                        fontSize: '13px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      <span>⚙️</span>
                      <span style={{ flex: 1 }}>{session.name}</span>
                      <span style={{ fontSize: '11px', color: '#666' }}>
                        {transformations.length} transformation(s)
                      </span>
                    </div>
                    {isSessionSelected && (
                      <div style={{ marginLeft: '20px', marginTop: '5px' }}>
                        {transformations.length === 0 ? (
                          <div style={{ 
                            padding: '8px', 
                            color: '#666', 
                            fontSize: '11px', 
                            fontStyle: 'italic' 
                          }}>
                            No transformations found
                          </div>
                        ) : (
                          transformations.map((transformation, tIdx) => {
                            const transformationName = transformation.transformation_name || transformation.mapping_name || transformation.name;
                            const isSelected = selectedMapping === transformationName;
                            return (
                              <div
                                key={tIdx}
                                onClick={() => handleMappingSelect(transformation)}
                                style={{
                                  padding: '8px',
                                  marginBottom: '5px',
                                  background: isSelected ? '#E3F2FD' : 'white',
                                  border: isSelected ? '2px solid #4A90E2' : '1px solid #ddd',
                                  borderRadius: '4px',
                                  cursor: 'pointer',
                                  fontSize: '12px',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '6px',
                                  transition: 'all 0.2s'
                                }}
                                onMouseEnter={(e) => {
                                  if (!isSelected) {
                                    e.currentTarget.style.background = '#f0f0f0';
                                  }
                                }}
                                onMouseLeave={(e) => {
                                  if (!isSelected) {
                                    e.currentTarget.style.background = 'white';
                                  }
                                }}
                              >
                                <span>📋</span>
                                <span style={{ flex: 1 }}>{transformationName || 'Unknown'}</span>
                              </div>
                            );
                          })
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Code Files and Content */}
        <div style={{ 
          flex: 1, 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          overflow: 'hidden',
          background: 'white',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {!selectedMapping ? (
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
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>💻</div>
              <h2 style={{ margin: '10px 0', color: '#333' }}>Select a Transformation</h2>
              <p style={{ margin: '5px 0', color: '#666' }}>
                Navigate: Workflow → Task → Transformation to view generated code files
              </p>
            </div>
          ) : (
            <>
              {/* Code Files List */}
              <div style={{ 
                borderBottom: '1px solid #ddd',
                padding: '15px',
                background: '#f5f5f5',
                maxHeight: '200px',
                overflow: 'auto'
              }}>
                <div style={{ fontWeight: 'bold', marginBottom: '10px', fontSize: '14px' }}>
                  Code Files for: {selectedMapping}
                </div>
                {loadingCode ? (
                  <div style={{ padding: '20px', textAlign: 'center' }}>Loading files...</div>
                ) : codeFiles.length === 0 ? (
                  <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                    <div style={{ fontSize: '24px', marginBottom: '10px' }}>📭</div>
                    <div>No code files found for {selectedMapping}</div>
                    <div style={{ fontSize: '11px', marginTop: '5px', color: '#999' }}>
                      Code may not have been generated yet for this transformation
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    {codeFiles.map((file, idx) => (
                      <div
                        key={idx}
                        onClick={() => handleCodeFileSelect(file)}
                        style={{
                          padding: '8px 12px',
                          background: selectedCodeFile?.file_path === file.file_path ? '#E3F2FD' : 'white',
                          border: selectedCodeFile?.file_path === file.file_path ? '2px solid #4A90E2' : '1px solid #ddd',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}
                      >
                        <span style={{ fontFamily: 'monospace' }}>
                          📄 {getFileName(file.file_path)}
                        </span>
                        <span style={{ 
                          padding: '2px 6px',
                          borderRadius: '3px',
                          background: '#4A90E2',
                          color: 'white',
                          fontSize: '10px'
                        }}>
                          {file.code_type}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Code Content */}
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
                ) : codeContent ? (
                  <div>
                    {selectedCodeFile && (
                      <div style={{ 
                        marginBottom: '15px', 
                        padding: '10px', 
                        background: '#f5f5f5', 
                        borderRadius: '4px',
                        fontSize: '13px'
                      }}>
                        <div><strong>File:</strong> {selectedCodeFile.file_path}</div>
                        {selectedCodeFile.quality_score !== null && selectedCodeFile.quality_score !== undefined && (
                          <div style={{ marginTop: '5px' }}>
                            <strong>Quality Score:</strong>{' '}
                            <span style={{ 
                              padding: '2px 6px',
                              borderRadius: '3px',
                              background: selectedCodeFile.quality_score >= 80 ? '#4CAF50' : 
                                         selectedCodeFile.quality_score >= 60 ? '#FF9800' : '#F44336',
                              color: 'white',
                              fontSize: '12px'
                            }}>
                              {selectedCodeFile.quality_score}/100
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                    <pre style={{ 
                      margin: 0,
                      padding: '15px',
                      background: '#fafafa',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      overflow: 'auto',
                      fontSize: '13px',
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      wordWrap: 'break-word',
                      lineHeight: '1.5',
                      maxHeight: '100%'
                    }}>
                      <code style={{ display: 'block', whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>{codeContent || '// No code content available'}</code>
                    </pre>
                  </div>
                ) : (
                  <div style={{ 
                    padding: '40px', 
                    textAlign: 'center', 
                    color: '#666'
                  }}>
                    <div style={{ fontSize: '48px', marginBottom: '20px' }}>📄</div>
                    <h3>Select a Code File</h3>
                    <p>Choose a code file from the list above to view its contents.</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
