import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';

export default function LineagePage() {
  const [dagData, setDagData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [visualizationFormat, setVisualizationFormat] = useState('json');
  const [selectedNode, setSelectedNode] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [selectedFileInfo, setSelectedFileInfo] = useState(null);
  const [inputMode, setInputMode] = useState('select'); // 'select' or 'manual'

  // Load file ID from localStorage
  useEffect(() => {
    // Try both possible keys
    const storedFileId = localStorage.getItem('lastUploadedFileId') || localStorage.getItem('lastFileId');
    if (storedFileId) {
      setFileId(storedFileId);
      setInputMode('manual');
    }
  }, []);

  useEffect(() => {
    loadUploadedFiles();
  }, []);

  useEffect(() => {
    if (fileId && inputMode === 'select') {
      loadFileInfo(fileId);
    }
  }, [fileId, inputMode]);

  const loadUploadedFiles = async () => {
    setLoadingFiles(true);
    try {
      const result = await apiClient.listAllFiles('workflow');
      if (result.success) {
        setUploadedFiles(result.files || []);
      }
    } catch (err) {
      console.error('Error loading files:', err);
    } finally {
      setLoadingFiles(false);
    }
  };

  const loadFileInfo = async (fileId) => {
    try {
      const fileInfo = await apiClient.getFileInfo(fileId);
      setSelectedFileInfo(fileInfo);
      if (fileInfo.file_type !== 'workflow') {
        setError(`⚠️ This file is a "${fileInfo.file_type}", but Lineage & DAG Viewer requires a "workflow" file.`);
      } else {
        setError(null);
      }
    } catch (err) {
      console.error('Error loading file info:', err);
    }
  };

  const loadDAG = async () => {
    if (!fileId) {
      setError('Please upload a workflow file first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // First, get file info to check file type
      let fileInfo = null;
      try {
        fileInfo = await apiClient.getFileInfo(fileId);
      } catch (err) {
        console.warn('Could not get file info:', err);
      }

      // Check if it's a workflow file
      if (fileInfo && fileInfo.file_type && fileInfo.file_type !== 'workflow') {
        setError(`File type is "${fileInfo.file_type}", but workflow is required. Please upload a workflow XML file.`);
        setLoading(false);
        return;
      }

      // First, parse the workflow to get workflow data
      const parseResult = await apiClient.parseWorkflow(fileId);
      
      if (parseResult.success && parseResult.data) {
        // Build DAG from workflow data
        const dagResult = await apiClient.buildDAG(null, parseResult.data, fileId);
        
        if (dagResult.success) {
          setDagData(dagResult.dag);
        } else {
          setError(dagResult.message || 'Failed to build DAG');
        }
      } else {
        const errorMsg = parseResult.message || parseResult.errors?.join(', ') || 'Failed to parse workflow';
        setError(`Failed to parse workflow: ${errorMsg}`);
      }
    } catch (err) {
      const errorMessage = err.message || err.detail || 'Failed to load DAG';
      setError(`Error: ${errorMessage}. Make sure the file is a workflow XML file.`);
      console.error('DAG loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderGraph = () => {
    if (!dagData || !dagData.nodes || !dagData.edges) {
      return <p>No DAG data available</p>;
    }

    const nodes = dagData.nodes || [];
    const edges = dagData.edges || [];

    // Simple graph visualization using SVG
    // For production, consider using React Flow or D3.js
    const nodePositions = calculateNodePositions(nodes, edges);
    const width = 1200;
    const height = Math.max(600, nodes.length * 100);

    return (
      <div style={{ overflow: 'auto', border: '1px solid #ddd', borderRadius: '4px', padding: '20px' }}>
        <svg width={width} height={height} style={{ background: '#f9f9f9' }}>
          {/* Render edges first */}
          {edges.map((edge, idx) => {
            const fromNode = nodePositions[edge.from];
            const toNode = nodePositions[edge.to];
            if (!fromNode || !toNode) return null;

            return (
              <g key={`edge-${idx}`}>
                <line
                  x1={fromNode.x + 100}
                  y1={fromNode.y + 40}
                  x2={toNode.x}
                  y2={toNode.y + 40}
                  stroke="#666"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                />
                {edge.condition && (
                  <text
                    x={(fromNode.x + toNode.x) / 2}
                    y={(fromNode.y + toNode.y) / 2 - 5}
                    textAnchor="middle"
                    fontSize="10"
                    fill="#666"
                  >
                    {edge.condition}
                  </text>
                )}
              </g>
            );
          })}

          {/* Arrow marker definition */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#666" />
            </marker>
          </defs>

          {/* Render nodes */}
          {nodes.map((node, idx) => {
            const pos = nodePositions[node.id || node.name];
            if (!pos) return null;

            const nodeType = node.type || 'default';
            const nodeColor = getNodeColor(nodeType);
            const isSelected = selectedNode?.id === (node.id || node.name);

            return (
              <g
                key={`node-${idx}`}
                onClick={() => setSelectedNode(node)}
                style={{ cursor: 'pointer' }}
              >
                <rect
                  x={pos.x}
                  y={pos.y}
                  width="120"
                  height="80"
                  fill={isSelected ? '#4CAF50' : nodeColor}
                  stroke={isSelected ? '#2E7D32' : '#333'}
                  strokeWidth={isSelected ? '3' : '2'}
                  rx="5"
                />
                <text
                  x={pos.x + 60}
                  y={pos.y + 30}
                  textAnchor="middle"
                  fontSize="12"
                  fontWeight="bold"
                  fill="#333"
                >
                  {node.name || node.id}
                </text>
                <text
                  x={pos.x + 60}
                  y={pos.y + 50}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#666"
                >
                  {nodeType}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Node details panel */}
        {selectedNode && (
          <div style={{
            marginTop: '20px',
            padding: '15px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            background: '#f9f9f9'
          }}>
            <h3>Node Details</h3>
            <p><strong>Name:</strong> {selectedNode.name || selectedNode.id}</p>
            <p><strong>Type:</strong> {selectedNode.type || 'Unknown'}</p>
            {selectedNode.metadata && (
              <div>
                <strong>Metadata:</strong>
                <pre style={{ background: '#fff', padding: '10px', borderRadius: '4px', fontSize: '12px' }}>
                  {JSON.stringify(selectedNode.metadata, null, 2)}
                </pre>
              </div>
            )}
            <button
              onClick={() => setSelectedNode(null)}
              style={{
                marginTop: '10px',
                padding: '5px 15px',
                background: '#666',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Close
            </button>
          </div>
        )}

        {/* Execution levels */}
        {dagData.execution_levels && dagData.execution_levels.length > 0 && (
          <div style={{ marginTop: '20px' }}>
            <h3>Execution Levels (Parallel Execution Groups)</h3>
            {dagData.execution_levels.map((level, idx) => (
              <div key={`level-${idx}`} style={{
                margin: '10px 0',
                padding: '10px',
                background: '#e3f2fd',
                borderRadius: '4px'
              }}>
                <strong>Level {idx + 1}:</strong> {level.join(', ')}
              </div>
            ))}
          </div>
        )}

        {/* Topological order */}
        {dagData.topological_order && dagData.topological_order.length > 0 && (
          <div style={{ marginTop: '20px' }}>
            <h3>Execution Order</h3>
            <p>{dagData.topological_order.join(' → ')}</p>
          </div>
        )}
      </div>
    );
  };

  const calculateNodePositions = (nodes, edges) => {
    // Simple layout algorithm: hierarchical layout
    const positions = {};
    const levels = {};
    const nodeLevels = {};

    // Calculate levels using BFS
    const inDegree = {};
    const adjacencyList = {};

    nodes.forEach(node => {
      const nodeId = node.id || node.name;
      inDegree[nodeId] = 0;
      adjacencyList[nodeId] = [];
    });

    edges.forEach(edge => {
      const from = edge.from;
      const to = edge.to;
      if (adjacencyList[from]) {
        adjacencyList[from].push(to);
        inDegree[to] = (inDegree[to] || 0) + 1;
      }
    });

    // Find root nodes (in-degree = 0)
    const queue = [];
    nodes.forEach(node => {
      const nodeId = node.id || node.name;
      if (inDegree[nodeId] === 0) {
        queue.push({ nodeId, level: 0 });
        nodeLevels[nodeId] = 0;
      }
    });

    // BFS to assign levels
    while (queue.length > 0) {
      const { nodeId, level } = queue.shift();
      if (adjacencyList[nodeId]) {
        adjacencyList[nodeId].forEach(neighbor => {
          if (nodeLevels[neighbor] === undefined) {
            nodeLevels[neighbor] = level + 1;
            queue.push({ nodeId: neighbor, level: level + 1 });
          }
        });
      }
    }

    // Group nodes by level
    Object.keys(nodeLevels).forEach(nodeId => {
      const level = nodeLevels[nodeId];
      if (!levels[level]) {
        levels[level] = [];
      }
      levels[level].push(nodeId);
    });

    // Position nodes
    const levelWidth = 250;
    const nodeHeight = 100;
    Object.keys(levels).forEach(level => {
      const levelNodes = levels[level];
      const startY = 50;
      const spacing = Math.max(120, (600 - startY) / levelNodes.length);

      levelNodes.forEach((nodeId, idx) => {
        positions[nodeId] = {
          x: parseInt(level) * levelWidth + 50,
          y: startY + idx * spacing
        };
      });
    });

    return positions;
  };

  const getNodeColor = (nodeType) => {
    const colors = {
      'Session': '#dae8fc',
      'Worklet': '#fff2cc',
      'Mapping': '#d5e8d4',
      'Command': '#ffe6cc',
      'Event': '#f8cecc',
      'Timer': '#e1d5e7',
      'default': '#f5f5f5'
    };
    return colors[nodeType] || colors.default;
  };

  const exportDAG = async (format) => {
    if (!fileId) {
      setError('Please upload a workflow file first');
      return;
    }

    try {
      const parseResult = await apiClient.parseWorkflow(fileId);
      if (parseResult.success && parseResult.data) {
        const visualization = await apiClient.visualizeDAG(null, parseResult.data, fileId, format, false);
        
        // Download as file
        const blob = new Blob([typeof visualization === 'string' ? visualization : JSON.stringify(visualization, null, 2)], {
          type: format === 'json' ? 'application/json' : 'text/plain'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dag.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      setError(err.message || 'Failed to export DAG');
    }
  };

  const getFileTypeColor = (type) => {
    return type === 'workflow' ? '#50C878' : '#FF6B6B';
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #ddd', paddingBottom: '15px' }}>
        <h2 style={{ margin: 0, color: '#333' }}>Lineage & DAG Viewer</h2>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          Visualize workflow execution graphs and data lineage. <strong>Requires a workflow XML file.</strong>
        </p>
      </div>

      {/* File Selection */}
      <div style={{ 
        marginBottom: '20px', 
        padding: '20px', 
        background: '#f5f5f5', 
        borderRadius: '8px',
        border: '1px solid #ddd'
      }}>
        <div style={{ marginBottom: '15px', display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={() => setInputMode('select')}
            style={{
              padding: '8px 16px',
              backgroundColor: inputMode === 'select' ? '#4A90E2' : '#f5f5f5',
              color: inputMode === 'select' ? 'white' : '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: inputMode === 'select' ? 'bold' : 'normal'
            }}
          >
            📁 Select from Uploaded Workflows
          </button>
          <button
            onClick={() => setInputMode('manual')}
            style={{
              padding: '8px 16px',
              backgroundColor: inputMode === 'manual' ? '#4A90E2' : '#f5f5f5',
              color: inputMode === 'manual' ? 'white' : '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: inputMode === 'manual' ? 'bold' : 'normal'
            }}
          >
            ✏️ Enter File ID Manually
          </button>
        </div>

        {inputMode === 'select' && (
          <div>
            <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
              Select Workflow File:
            </label>
            {loadingFiles ? (
              <div style={{ padding: '10px', textAlign: 'center' }}>Loading workflow files...</div>
            ) : uploadedFiles.length === 0 ? (
              <div style={{ padding: '15px', background: '#fff3cd', borderRadius: '4px', color: '#856404' }}>
                No workflow files found. Upload workflow files in the File Browser or Upload & Parse tab.
              </div>
            ) : (
              <select
                value={fileId || ''}
                onChange={(e) => {
                  setFileId(e.target.value);
                  setDagData(null);
                  setError(null);
                }}
                style={{
                  padding: '10px',
                  width: '100%',
                  maxWidth: '600px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                <option value="">-- Select a workflow file --</option>
                {uploadedFiles.map((f) => (
                  <option key={f.file_id} value={f.file_id}>
                    🔄 {f.filename} - {new Date(f.uploaded_at).toLocaleDateString()}
                  </option>
                ))}
              </select>
            )}
            {selectedFileInfo && (
              <div style={{ 
                marginTop: '15px', 
                padding: '10px', 
                background: selectedFileInfo.file_type === 'workflow' ? '#d4edda' : '#f8d7da',
                borderRadius: '4px',
                border: `2px solid ${getFileTypeColor(selectedFileInfo.file_type)}`
              }}>
                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                  Selected: {selectedFileInfo.filename}
                </div>
                <div style={{ fontSize: '12px' }}>
                  Type: <span style={{
                    padding: '2px 8px',
                    background: getFileTypeColor(selectedFileInfo.file_type),
                    color: 'white',
                    borderRadius: '3px',
                    fontWeight: 'bold'
                  }}>{selectedFileInfo.file_type}</span>
                  {selectedFileInfo.file_type !== 'workflow' && (
                    <span style={{ color: '#c62828', marginLeft: '10px' }}>
                      ⚠️ This is not a workflow file!
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {inputMode === 'manual' && (
          <div>
            <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
              File ID:
            </label>
            <input
              type="text"
              value={fileId || ''}
              onChange={(e) => {
                setFileId(e.target.value);
                setDagData(null);
                setError(null);
                setSelectedFileInfo(null);
              }}
              placeholder="Enter workflow file ID"
              style={{ 
                padding: '10px', 
                width: '100%', 
                maxWidth: '600px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </div>
        )}

        <div style={{ marginTop: '15px' }}>
          <button
            onClick={loadDAG}
            disabled={loading || !fileId || (selectedFileInfo && selectedFileInfo.file_type !== 'workflow')}
            style={{
              padding: '10px 20px',
              background: (loading || !fileId || (selectedFileInfo && selectedFileInfo.file_type !== 'workflow')) ? '#ccc' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: (loading || !fileId || (selectedFileInfo && selectedFileInfo.file_type !== 'workflow')) ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '14px'
            }}
          >
            {loading ? 'Loading DAG...' : '🔄 Load DAG'}
          </button>
        </div>
      </div>

        <div style={{ marginTop: '10px' }}>
          <label style={{ marginRight: '10px' }}>Export Format:</label>
          <select
            value={visualizationFormat}
            onChange={(e) => setVisualizationFormat(e.target.value)}
            style={{ padding: '5px', marginRight: '10px' }}
          >
            <option value="json">JSON</option>
            <option value="dot">DOT</option>
            <option value="mermaid">Mermaid</option>
            <option value="svg">SVG</option>
          </select>
          <button
            onClick={() => exportDAG(visualizationFormat)}
            disabled={!dagData}
            style={{
              padding: '5px 15px',
              background: !dagData ? '#ccc' : '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: !dagData ? 'not-allowed' : 'pointer'
            }}
          >
            Export DAG
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '15px',
          background: '#ffebee',
          color: '#c62828',
          borderRadius: '4px',
          marginBottom: '20px',
          border: '1px solid #ef5350'
        }}>
          <strong>Error:</strong> {error}
          {!error.includes('⚠️') && (
            <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
              <strong>Note:</strong> The Lineage & DAG Viewer requires a <strong>workflow</strong> XML file.
              <br />
              Select a workflow file from the dropdown above, or upload one in the File Browser tab.
            </div>
          )}
        </div>
      )}

      {loading && (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <p>Loading DAG...</p>
        </div>
      )}

      {!loading && dagData && renderGraph()}

      {!loading && !dagData && !error && (
        <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
          <p>No DAG data loaded. Please upload a workflow file and click "Load DAG".</p>
        </div>
      )}
    </div>
  );
}
