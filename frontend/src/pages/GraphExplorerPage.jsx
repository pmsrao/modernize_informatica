import React, { useState, useEffect } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  Panel,
  MarkerType 
} from 'reactflow';
import 'reactflow/dist/style.css';
import apiClient from '../services/api.js';

const nodeTypes = {
  mapping: ({ data }) => (
    <div style={{
      padding: '10px',
      background: '#4A90E2',
      color: 'white',
      borderRadius: '8px',
      border: '2px solid #2E5C8A',
      minWidth: '150px',
      textAlign: 'center',
      fontWeight: 'bold'
    }}>
      <div>{data.label}</div>
      <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.9 }}>
        {data.complexity || 'Mapping'}
      </div>
    </div>
  ),
  source: ({ data }) => (
    <div style={{
      padding: '8px',
      background: '#50C878',
      color: 'white',
      borderRadius: '8px',
      border: '2px solid #2E7D4E',
      minWidth: '120px',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '12px', fontWeight: 'bold' }}>{data.label}</div>
      {data.table && (
        <div style={{ fontSize: '10px', marginTop: '3px', opacity: 0.9 }}>
          {data.table}
        </div>
      )}
    </div>
  ),
  target: ({ data }) => (
    <div style={{
      padding: '8px',
      background: '#FF6B6B',
      color: 'white',
      borderRadius: '8px',
      border: '2px solid #C92A2A',
      minWidth: '120px',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '12px', fontWeight: 'bold' }}>{data.label}</div>
      {data.table && (
        <div style={{ fontSize: '10px', marginTop: '3px', opacity: 0.9 }}>
          {data.table}
        </div>
      )}
    </div>
  ),
  transformation: ({ data }) => {
    const colors = {
      'Expression': '#FFA500',
      'Lookup': '#9B59B6',
      'Aggregator': '#3498DB',
      'Joiner': '#E74C3C',
      'Router': '#1ABC9C',
      'Filter': '#F39C12',
      'Union': '#16A085',
      'SourceQualifier': '#34495E',
      'UpdateStrategy': '#E67E22',
      'Sorter': '#95A5A6',
      'Rank': '#D35400'
    };
    const bgColor = colors[data.transformation_type] || '#7F8C8D';
    
    return (
      <div style={{
        padding: '8px',
        background: bgColor,
        color: 'white',
        borderRadius: '8px',
        border: '2px solid #555',
        minWidth: '120px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '12px', fontWeight: 'bold' }}>{data.label}</div>
        <div style={{ fontSize: '10px', marginTop: '3px', opacity: 0.9 }}>
          {data.transformation_type || 'Transformation'}
        </div>
      </div>
    );
  }
};

export default function GraphExplorerPage() {
  const [mappings, setMappings] = useState([]);
  const [selectedMapping, setSelectedMapping] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState('list'); // 'list', 'graph', 'details'
  const [statistics, setStatistics] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    loadMappings();
    loadStatistics();
  }, []);

  useEffect(() => {
    if (selectedMapping) {
      loadMappingStructure(selectedMapping);
    }
  }, [selectedMapping]);

  const loadMappings = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.listMappings();
      if (result.success) {
        setMappings(result.mappings || []);
      }
    } catch (err) {
      setError(err.message || 'Failed to load mappings');
      console.error('Error loading mappings:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const result = await apiClient.getGraphStatistics();
      if (result.success) {
        setStatistics(result.statistics);
      }
    } catch (err) {
      console.error('Error loading statistics:', err);
    }
  };

  const loadMappingStructure = async (mappingName) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.getMappingStructure(mappingName);
      if (result.success && result.graph) {
        console.log('Graph data received:', {
          nodes: result.graph.nodes.length,
          edges: result.graph.edges.length,
          edges_sample: result.graph.edges.slice(0, 3)
        });
        
        // Convert to React Flow format
        const nodes = result.graph.nodes.map((node, idx) => ({
          id: node.id,
          type: node.type,
          data: { ...node.data, label: node.label },
          position: { x: 0, y: 0 } // Will be calculated by layout
        }));

        // Filter to only show data flow edges (FLOWS_TO), hide structural edges
        const dataFlowEdges = result.graph.edges.filter(edge => 
          edge.type === 'flows_to' || edge.label === 'FLOWS_TO'
        );
        
        const edges = dataFlowEdges.map((edge, idx) => {
          // Data flow edges - make them prominent
          return {
            id: edge.id,
            source: edge.source,
            target: edge.target,
            type: 'smoothstep',
            animated: true,
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 20,
              height: 20,
              color: '#4A90E2'
            },
            style: { 
              stroke: '#4A90E2', 
              strokeWidth: 4,
              opacity: 0.8
            },
            label: edge.data?.from_port && edge.data?.to_port 
              ? `${edge.data.from_port} → ${edge.data.to_port}`
              : '',
            labelStyle: {
              fill: '#4A90E2',
              fontWeight: 600,
              fontSize: '11px'
            },
            labelBgStyle: {
              fill: 'white',
              fillOpacity: 0.8
            }
          };
        });

        console.log('Processed edges:', edges.length, 'edges created');
        console.log('Sample edges:', edges.slice(0, 5));
        console.log('Edge details:', edges.map(e => ({ id: e.id, source: e.source, target: e.target, type: e.type })).slice(0, 10));

        // Simple layout: hierarchical
        layoutNodes(nodes, edges);
        
        setGraphData({ nodes, edges });
        setView('graph');
      } else {
        console.error('No graph data in response:', result);
        setError('No graph data received from server');
      }
    } catch (err) {
      setError(err.message || 'Failed to load mapping structure');
      console.error('Error loading mapping structure:', err);
    } finally {
      setLoading(false);
    }
  };

  const layoutNodes = (nodes, edges) => {
    // Hierarchical layout based on data flow
    const mappingNode = nodes.find(n => n.type === 'mapping');
    if (!mappingNode) return;

    const sources = nodes.filter(n => n.type === 'source');
    const targets = nodes.filter(n => n.type === 'target');
    const transformations = nodes.filter(n => n.type === 'transformation');

    // Build adjacency list to determine levels
    const adjacency = {};
    const inDegree = {};
    
    nodes.forEach(node => {
      adjacency[node.id] = [];
      inDegree[node.id] = 0;
    });
    
    edges.forEach(edge => {
      if (edge.type === 'flows_to' || edge.type === 'FLOWS_TO') {
        if (adjacency[edge.source]) {
          adjacency[edge.source].push(edge.target);
          inDegree[edge.target] = (inDegree[edge.target] || 0) + 1;
        }
      }
    });

    // Assign levels using BFS
    const levels = {};
    const queue = [];
    
    // Sources are level 0
    sources.forEach(source => {
      levels[source.id] = 0;
      queue.push({ id: source.id, level: 0 });
    });
    
    // If no sources, start with nodes that have no incoming edges
    if (sources.length === 0) {
      nodes.forEach(node => {
        if (inDegree[node.id] === 0 && node.type !== 'mapping') {
          levels[node.id] = 0;
          queue.push({ id: node.id, level: 0 });
        }
      });
    }
    
    // BFS to assign levels
    while (queue.length > 0) {
      const { id, level } = queue.shift();
      if (adjacency[id]) {
        adjacency[id].forEach(neighbor => {
          if (levels[neighbor] === undefined) {
            levels[neighbor] = level + 1;
            queue.push({ id: neighbor, level: level + 1 });
          }
        });
      }
    }

    // Position mapping at top center (but make it smaller/less prominent)
    mappingNode.position = { x: 50, y: 50 };

    // Position nodes by level
    const levelWidth = 300;
    const startX = 200;
    const startY = 150;
    const verticalSpacing = 100;

    const nodesByLevel = {};
    nodes.forEach(node => {
      if (node.type !== 'mapping') {
        const level = levels[node.id] !== undefined ? levels[node.id] : 1;
        if (!nodesByLevel[level]) {
          nodesByLevel[level] = [];
        }
        nodesByLevel[level].push(node);
      }
    });

    Object.keys(nodesByLevel).sort((a, b) => parseInt(a) - parseInt(b)).forEach(level => {
      const levelNodes = nodesByLevel[level];
      levelNodes.forEach((node, idx) => {
        node.position = {
          x: startX + parseInt(level) * levelWidth,
          y: startY + idx * verticalSpacing
        };
      });
    });
  };

  const filteredMappings = mappings.filter(m => 
    m.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.mapping_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleNodeClick = (event, node) => {
    setSelectedNode(node);
  };

  return (
    <div style={{ padding: '20px', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h1 style={{ margin: 0, color: '#333' }}>Graph Explorer</h1>
        <p style={{ margin: '5px 0', color: '#666' }}>
          Navigate and visualize canonical models stored in Neo4j
        </p>
      </div>

      {statistics && (
        <div style={{ 
          display: 'flex', 
          gap: '20px', 
          marginBottom: '20px',
          padding: '15px',
          background: '#f5f5f5',
          borderRadius: '8px'
        }}>
          <div>
            <strong>Total Mappings:</strong> {statistics.total_mappings || 0}
          </div>
          <div>
            <strong>Total Transformations:</strong> {statistics.total_transformations || 0}
          </div>
          <div>
            <strong>Total Tables:</strong> {statistics.total_tables || 0}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '20px', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <div style={{ 
          width: '300px', 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          padding: '15px',
          overflow: 'auto',
          background: 'white'
        }}>
          <div style={{ marginBottom: '15px' }}>
            <input
              type="text"
              placeholder="Search mappings..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </div>

          <div style={{ marginBottom: '10px', fontSize: '12px', color: '#666' }}>
            {filteredMappings.length} mapping(s) found
          </div>

          {loading && <div style={{ padding: '10px', textAlign: 'center' }}>Loading...</div>}
          {error && <div style={{ padding: '10px', color: 'red', fontSize: '12px' }}>{error}</div>}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {filteredMappings.map((mapping) => (
              <div
                key={mapping.name}
                onClick={() => {
                  setSelectedMapping(mapping.name);
                  setView('graph');
                }}
                style={{
                  padding: '12px',
                  border: selectedMapping === mapping.name ? '2px solid #4A90E2' : '1px solid #ddd',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  background: selectedMapping === mapping.name ? '#E3F2FD' : 'white',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (selectedMapping !== mapping.name) {
                    e.currentTarget.style.background = '#f5f5f5';
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedMapping !== mapping.name) {
                    e.currentTarget.style.background = 'white';
                  }
                }}
              >
                <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '5px' }}>
                  {mapping.mapping_name || mapping.name}
                </div>
                <div style={{ fontSize: '11px', color: '#666' }}>
                  <div>Complexity: {mapping.complexity || 'N/A'}</div>
                  <div>Sources: {mapping.source_count || 0} | Targets: {mapping.target_count || 0}</div>
                  <div>Transformations: {mapping.transformation_count || 0}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content Area */}
        <div style={{ flex: 1, border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', position: 'relative' }}>
          {view === 'list' && !selectedMapping && (
            <div style={{ 
              padding: '40px', 
              textAlign: 'center', 
              color: '#666',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div>
                <h2>Select a mapping to visualize</h2>
                <p>Choose a mapping from the sidebar to view its graph structure</p>
              </div>
            </div>
          )}

          {view === 'graph' && selectedMapping && (
            <>
              <div style={{ 
                position: 'absolute', 
                top: '10px', 
                left: '10px', 
                zIndex: 10,
                background: 'white',
                padding: '10px',
                borderRadius: '6px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}>
                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                  {selectedMapping}
                </div>
                <button
                  onClick={() => {
                    setView('list');
                    setSelectedMapping(null);
                    setSelectedNode(null);
                  }}
                  style={{
                    padding: '5px 10px',
                    background: '#4A90E2',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Back to List
                </button>
              </div>

              {loading ? (
                <div style={{ 
                  padding: '40px', 
                  textAlign: 'center',
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  Loading graph...
                </div>
              ) : error ? (
                <div style={{ 
                  padding: '40px', 
                  textAlign: 'center',
                  color: 'red',
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {error}
                </div>
              ) : (
                <ReactFlow
                  nodes={graphData.nodes}
                  edges={graphData.edges}
                  nodeTypes={nodeTypes}
                  edgeTypes={{}}
                  onNodeClick={handleNodeClick}
                  fitView
                  style={{ background: '#fafafa' }}
                  defaultEdgeOptions={{
                    animated: true,
                    style: { strokeWidth: 2 }
                  }}
                >
                  <Background />
                  <Controls />
                  <MiniMap />
                </ReactFlow>
              )}
            </>
          )}
        </div>

        {/* Details Panel */}
        {selectedNode && (
          <div style={{ 
            width: '300px', 
            border: '1px solid #ddd', 
            borderRadius: '8px',
            padding: '15px',
            overflow: 'auto',
            background: 'white'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '15px',
              borderBottom: '1px solid #ddd',
              paddingBottom: '10px'
            }}>
              <h3 style={{ margin: 0, fontSize: '16px' }}>Node Details</h3>
              <button
                onClick={() => setSelectedNode(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '20px',
                  cursor: 'pointer',
                  color: '#666'
                }}
              >
                ×
              </button>
            </div>
            <div style={{ fontSize: '14px' }}>
              <div style={{ marginBottom: '10px' }}>
                <strong>Type:</strong> {selectedNode.data?.type || selectedNode.type}
              </div>
              <div style={{ marginBottom: '10px' }}>
                <strong>Name:</strong> {selectedNode.data?.name || selectedNode.data?.label}
              </div>
              {selectedNode.data?.table && (
                <div style={{ marginBottom: '10px' }}>
                  <strong>Table:</strong> {selectedNode.data.table}
                </div>
              )}
              {selectedNode.data?.transformation_type && (
                <div style={{ marginBottom: '10px' }}>
                  <strong>Transformation Type:</strong> {selectedNode.data.transformation_type}
                </div>
              )}
              {selectedNode.data?.complexity && (
                <div style={{ marginBottom: '10px' }}>
                  <strong>Complexity:</strong> {selectedNode.data.complexity}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
