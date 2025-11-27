import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';

export default function LineagePage() {
  const [dagData, setDagData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [visualizationFormat, setVisualizationFormat] = useState('json');
  const [selectedNode, setSelectedNode] = useState(null);

  // Load file ID from localStorage
  useEffect(() => {
    const storedFileId = localStorage.getItem('lastFileId');
    if (storedFileId) {
      setFileId(storedFileId);
    }
  }, []);

  const loadDAG = async () => {
    if (!fileId) {
      setError('Please upload a workflow file first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
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
        setError('Failed to parse workflow');
      }
    } catch (err) {
      setError(err.message || 'Failed to load DAG');
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

  return (
    <div style={{ padding: '20px' }}>
      <h2>Lineage & DAG Viewer</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <div style={{ marginBottom: '10px' }}>
          <label style={{ marginRight: '10px' }}>File ID:</label>
          <input
            type="text"
            value={fileId || ''}
            onChange={(e) => setFileId(e.target.value)}
            placeholder="Enter file ID or upload a file"
            style={{ padding: '5px', width: '300px', marginRight: '10px' }}
          />
          <button
            onClick={loadDAG}
            disabled={loading || !fileId}
            style={{
              padding: '5px 15px',
              background: loading ? '#ccc' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginRight: '10px'
            }}
          >
            {loading ? 'Loading...' : 'Load DAG'}
          </button>
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
          padding: '10px',
          background: '#ffebee',
          color: '#c62828',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
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
