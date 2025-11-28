import React, { useState, useEffect } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  MarkerType 
} from 'reactflow';
import 'reactflow/dist/style.css';
import apiClient from '../services/api.js';

const nodeTypes = {
  workflow: ({ data }) => (
    <div style={{
      padding: '12px',
      background: '#4A90E2',
      color: 'white',
      borderRadius: '10px',
      border: '3px solid #2E5C8A',
      minWidth: '180px',
      textAlign: 'center',
      fontWeight: 'bold',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
    }}>
      <div style={{ fontSize: '16px', marginBottom: '5px' }}>🔄</div>
      <div style={{ fontSize: '14px' }}>{data.label}</div>
      <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.9 }}>
        Workflow
      </div>
      {data.tasks_count !== undefined && (
        <div style={{ fontSize: '10px', marginTop: '3px', opacity: 0.8 }}>
          {data.tasks_count} task(s)
        </div>
      )}
    </div>
  ),
  worklet: ({ data }) => (
    <div style={{
      padding: '12px',
      background: '#9B59B6',
      color: 'white',
      borderRadius: '10px',
      border: '3px solid #6C3483',
      minWidth: '180px',
      textAlign: 'center',
      fontWeight: 'bold',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
    }}>
      <div style={{ fontSize: '16px', marginBottom: '5px' }}>📦</div>
      <div style={{ fontSize: '14px' }}>{data.label}</div>
      <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.9 }}>
        Worklet
      </div>
      {data.tasks_count !== undefined && (
        <div style={{ fontSize: '10px', marginTop: '3px', opacity: 0.8 }}>
          {data.tasks_count} task(s)
        </div>
      )}
    </div>
  ),
  session: ({ data }) => (
    <div style={{
      padding: '12px',
      background: '#FFA500',
      color: 'white',
      borderRadius: '10px',
      border: '3px solid #CC7700',
      minWidth: '180px',
      textAlign: 'center',
      fontWeight: 'bold',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
    }}>
      <div style={{ fontSize: '16px', marginBottom: '5px' }}>⚙️</div>
      <div style={{ fontSize: '14px' }}>{data.label}</div>
      <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.9 }}>
        Session
      </div>
      {data.mapping_name && (
        <div style={{ fontSize: '10px', marginTop: '3px', opacity: 0.8 }}>
          → {data.mapping_name}
        </div>
      )}
    </div>
  ),
  mapping: ({ data }) => (
    <div style={{
      padding: '12px',
      background: '#50C878',
      color: 'white',
      borderRadius: '10px',
      border: '3px solid #2E7D4E',
      minWidth: '180px',
      textAlign: 'center',
      fontWeight: 'bold',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
    }}>
      <div style={{ fontSize: '16px', marginBottom: '5px' }}>📋</div>
      <div style={{ fontSize: '14px' }}>{data.label}</div>
      <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.9 }}>
        Mapping
      </div>
      {(data.sources_count !== undefined || data.targets_count !== undefined) && (
        <div style={{ fontSize: '10px', marginTop: '3px', opacity: 0.8 }}>
          {data.sources_count || 0} source(s) → {data.targets_count || 0} target(s)
        </div>
      )}
      {data.transformations_count !== undefined && (
        <div style={{ fontSize: '10px', marginTop: '2px', opacity: 0.8 }}>
          {data.transformations_count} transformation(s)
        </div>
      )}
    </div>
  )
};

export default function HierarchyPage() {
  const [hierarchy, setHierarchy] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [statistics, setStatistics] = useState(null);

  useEffect(() => {
    loadHierarchy();
  }, []);

  const loadHierarchy = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.getHierarchy();
      if (result.success && result.hierarchy) {
        const graphData = result.hierarchy;
        
        // Convert to React Flow format with hierarchical layout
        const nodes = graphData.nodes.map((node, idx) => ({
          id: node.id,
          type: node.type,
          data: { ...node.data, label: node.label },
          position: { x: 0, y: 0 } // Will be calculated
        }));

        const edges = graphData.edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: 'smoothstep',
          animated: true,
          markerEnd: {
            type: MarkerType.ArrowClosed,
          },
          style: { stroke: '#666', strokeWidth: 3 },
          label: edge.label || ''
        }));

        // Layout nodes hierarchically
        layoutNodes(nodes, edges);
        
        setHierarchy({ nodes, edges });
        setStatistics(graphData.statistics);
      }
    } catch (err) {
      setError(err.message || 'Failed to load hierarchy');
      console.error('Error loading hierarchy:', err);
    } finally {
      setLoading(false);
    }
  };

  const layoutNodes = (nodes, edges) => {
    // Hierarchical layout: Workflow -> Worklet -> Session -> Mapping
    const levels = {
      workflow: 0,
      worklet: 1,
      session: 2,
      mapping: 3
    };

    // Group nodes by type
    const nodesByType = {
      workflow: [],
      worklet: [],
      session: [],
      mapping: []
    };

    nodes.forEach(node => {
      const type = node.type;
      if (nodesByType[type]) {
        nodesByType[type].push(node);
      }
    });

    // Position nodes
    const levelWidth = 300;
    const startX = 100;
    const startY = 100;
    const verticalSpacing = 150;

    Object.keys(nodesByType).forEach(type => {
      const typeNodes = nodesByType[type];
      const level = levels[type];
      
      typeNodes.forEach((node, idx) => {
        node.position = {
          x: startX + level * levelWidth,
          y: startY + idx * verticalSpacing
        };
      });
    });
  };

  const handleNodeClick = (event, node) => {
    setSelectedNode(node);
  };

  return (
    <div style={{ padding: '20px', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #ddd', paddingBottom: '15px' }}>
        <h1 style={{ margin: 0, color: '#333' }}>Informatica Hierarchy</h1>
        <p style={{ margin: '5px 0', color: '#666' }}>
          Visualize the component hierarchy: Workflow → Worklet → Session → Mapping
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
            <strong>🔄 Workflows:</strong> {statistics.workflows || 0}
          </div>
          <div>
            <strong>📦 Worklets:</strong> {statistics.worklets || 0}
          </div>
          <div>
            <strong>⚙️ Sessions:</strong> {statistics.sessions || 0}
          </div>
          <div>
            <strong>📋 Mappings:</strong> {statistics.mappings || 0}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '20px', flex: 1, overflow: 'hidden' }}>
        {/* Main Graph Area */}
        <div style={{ flex: 1, border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', position: 'relative', background: '#fafafa' }}>
          {loading ? (
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
                <div>Loading hierarchy...</div>
              </div>
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
              <div>
                <div style={{ fontSize: '24px', marginBottom: '10px' }}>❌</div>
                <div>{error}</div>
                <button
                  onClick={loadHierarchy}
                  style={{
                    marginTop: '15px',
                    padding: '8px 16px',
                    background: '#4A90E2',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Retry
                </button>
              </div>
            </div>
          ) : hierarchy && hierarchy.nodes.length > 0 ? (
            <>
              <div style={{ 
                position: 'absolute', 
                top: '10px', 
                left: '10px', 
                zIndex: 10,
                background: 'white',
                padding: '10px',
                borderRadius: '6px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                fontSize: '12px'
              }}>
                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Legend:</div>
                <div>🔄 Workflow → 📦 Worklet → ⚙️ Session → 📋 Mapping</div>
              </div>
              <ReactFlow
                nodes={hierarchy.nodes}
                edges={hierarchy.edges}
                nodeTypes={nodeTypes}
                onNodeClick={handleNodeClick}
                fitView
                style={{ background: '#fafafa' }}
              >
                <Background />
                <Controls />
                <MiniMap />
              </ReactFlow>
            </>
          ) : (
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
                <div style={{ fontSize: '48px', marginBottom: '15px' }}>📁</div>
                <h3>No hierarchy data found</h3>
                <p>Upload Informatica XML files (workflows, worklets, sessions, mappings) to see the hierarchy.</p>
                <p style={{ fontSize: '12px', marginTop: '10px', color: '#999' }}>
                  Go to File Browser to upload files, then return here to view the hierarchy.
                </p>
              </div>
            </div>
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
              <h3 style={{ margin: 0, fontSize: '16px' }}>Component Details</h3>
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
                <strong>Type:</strong> {selectedNode.type}
              </div>
              <div style={{ marginBottom: '10px' }}>
                <strong>Name:</strong> {selectedNode.data?.name || selectedNode.data?.label}
              </div>
              {selectedNode.data?.file_id && (
                <div style={{ marginBottom: '10px' }}>
                  <strong>File ID:</strong>
                  <div style={{ 
                    fontFamily: 'monospace', 
                    fontSize: '11px', 
                    background: '#f5f5f5', 
                    padding: '4px 8px', 
                    borderRadius: '4px',
                    marginTop: '4px',
                    wordBreak: 'break-all'
                  }}>
                    {selectedNode.data.file_id}
                  </div>
                </div>
              )}
              {selectedNode.data?.tasks_count !== undefined && (
                <div style={{ marginBottom: '10px' }}>
                  <strong>Tasks:</strong> {selectedNode.data.tasks_count}
                </div>
              )}
              {selectedNode.data?.mapping_name && (
                <div style={{ marginBottom: '10px' }}>
                  <strong>Uses Mapping:</strong> {selectedNode.data.mapping_name}
                </div>
              )}
              {selectedNode.data?.sources_count !== undefined && (
                <div style={{ marginBottom: '10px' }}>
                  <strong>Sources:</strong> {selectedNode.data.sources_count}
                </div>
              )}
              {selectedNode.data?.targets_count !== undefined && (
                <div style={{ marginBottom: '10px' }}>
                  <strong>Targets:</strong> {selectedNode.data.targets_count}
                </div>
              )}
              {selectedNode.data?.transformations_count !== undefined && (
                <div style={{ marginBottom: '10px' }}>
                  <strong>Transformations:</strong> {selectedNode.data.transformations_count}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

