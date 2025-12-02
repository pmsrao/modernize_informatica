import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';

/**
 * Repository Structure Page
 * 
 * Displays uploaded files in a hierarchical tree structure showing
 * the relationships: Workflow -> Worklet -> Session -> Mapping
 */
export default function RepositoryStructurePage({ files, onFileAction, onParseAndEnhance }) {
  const [hierarchy, setHierarchy] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState(new Set());

  useEffect(() => {
    buildHierarchy();
  }, [files]);

  const buildHierarchy = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Get hierarchy from backend
      const result = await apiClient.getHierarchy();
      
      if (result.success && result.hierarchy) {
        setHierarchy(result.hierarchy);
        // Expand all nodes by default
        const allNodeIds = new Set();
        result.hierarchy.nodes?.forEach(node => allNodeIds.add(node.id));
        setExpandedNodes(allNodeIds);
      } else {
        // Build hierarchy from files if backend doesn't have it
        const hierarchyData = buildHierarchyFromFiles(files);
        setHierarchy(hierarchyData);
      }
    } catch (err) {
      console.error('Error loading hierarchy:', err);
      // Fallback to building from files
      const hierarchyData = buildHierarchyFromFiles(files);
      setHierarchy(hierarchyData);
    } finally {
      setLoading(false);
    }
  };

  const buildHierarchyFromFiles = (fileList) => {
    // Group files by type
    const workflows = fileList.filter(f => f.file_type === 'workflow');
    const worklets = fileList.filter(f => f.file_type === 'worklet');
    const sessions = fileList.filter(f => f.file_type === 'session');
    const mappings = fileList.filter(f => f.file_type === 'mapping');

    // Build tree structure
    const tree = [];
    
    workflows.forEach(wf => {
      const workflowNode = {
        id: wf.file_id,
        name: wf.filename,
        type: 'workflow',
        file: wf,
        children: []
      };

      // Find worklets (this is a simplified approach - in reality, we'd need to parse XML)
      // For now, we'll show all worklets as potential children
      worklets.forEach(wk => {
        const workletNode = {
          id: wk.file_id,
          name: wk.filename,
          type: 'worklet',
          file: wk,
          children: []
        };

        // Find sessions
        sessions.forEach(sess => {
          const sessionNode = {
            id: sess.file_id,
            name: sess.filename,
            type: 'session',
            file: sess,
            children: []
          };

          // Find mappings (simplified - would need XML parsing for actual relationships)
          mappings.forEach(map => {
            sessionNode.children.push({
              id: map.file_id,
              name: map.filename,
              type: 'mapping',
              file: map,
              children: []
            });
          });

          workletNode.children.push(sessionNode);
        });

        workflowNode.children.push(workletNode);
      });

      tree.push(workflowNode);
    });

    // Also show standalone items
    const standaloneWorklets = worklets.filter(wk => 
      !workflows.some(wf => wf.file_id === wk.file_id) // Not already in a workflow
    );
    const standaloneSessions = sessions.filter(sess => 
      !worklets.some(wk => wk.file_id === sess.file_id) // Not already in a worklet
    );
    const standaloneMappings = mappings.filter(map => 
      !sessions.some(sess => sess.file_id === map.file_id) // Not already in a session
    );

    return {
      tree,
      standalone: {
        worklets: standaloneWorklets,
        sessions: standaloneSessions,
        mappings: standaloneMappings
      }
    };
  };

  const toggleNode = (nodeId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const getTypeIcon = (type) => {
    const icons = {
      'workflow': '🔄',
      'worklet': '📦',
      'session': '⚙️',
      'mapping': '📋'
    };
    return icons[type] || '📄';
  };

  const getTypeColor = (type) => {
    const colors = {
      'workflow': '#4A90E2',
      'worklet': '#9B59B6',
      'session': '#FFA500',
      'mapping': '#50C878'
    };
    return colors[type] || '#95A5A6';
  };

  const renderTreeNode = (node, level = 0) => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children && node.children.length > 0;
    const indent = level * 24;

    return (
      <div key={node.id} style={{ marginLeft: `${indent}px` }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '8px',
            marginBottom: '4px',
            background: level === 0 ? '#f5f5f5' : 'white',
            borderRadius: '4px',
            border: `1px solid ${getTypeColor(node.type)}`,
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#f0f0f0';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = level === 0 ? '#f5f5f5' : 'white';
          }}
        >
          {hasChildren && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                toggleNode(node.id);
              }}
              style={{
                marginRight: '8px',
                fontSize: '12px',
                cursor: 'pointer',
                userSelect: 'none',
                width: '20px',
                textAlign: 'center'
              }}
            >
              {isExpanded ? '▼' : '▶'}
            </span>
          )}
          {!hasChildren && <span style={{ width: '20px', marginRight: '8px' }} />}
          
          <span style={{ fontSize: '20px', marginRight: '8px' }}>
            {getTypeIcon(node.type)}
          </span>
          
          <span style={{ flex: 1, fontWeight: level === 0 ? 'bold' : 'normal' }}>
            {node.name}
          </span>
          
          <span
            style={{
              padding: '4px 8px',
              background: getTypeColor(node.type),
              color: 'white',
              borderRadius: '4px',
              fontSize: '11px',
              marginRight: '8px',
              fontWeight: 'bold'
            }}
          >
            {node.type.toUpperCase()}
          </span>

          {node.file && (
            <div style={{ display: 'flex', gap: '5px' }}>
              {node.type === 'mapping' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onParseAndEnhance && onParseAndEnhance(node.file.file_id);
                  }}
                  style={{
                    padding: '4px 8px',
                    background: '#4A90E2',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '11px'
                  }}
                >
                  Parse
                </button>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onFileAction && onFileAction(node.file);
                }}
                style={{
                  padding: '4px 8px',
                  background: '#50C878',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '11px'
                }}
              >
                View
              </button>
            </div>
          )}
        </div>

        {hasChildren && isExpanded && (
          <div style={{ marginLeft: '20px' }}>
            {node.children.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div>Loading repository structure...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: '#c62828' }}>
        Error: {error}
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', height: '100%', overflow: 'auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ margin: 0, color: '#333' }}>Repository Structure</h2>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          Hierarchical view of Informatica components: Workflow → Worklet → Session → Mapping
        </p>
      </div>

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center' }}>
          <div>Loading repository structure...</div>
        </div>
      ) : hierarchy && hierarchy.nodes && hierarchy.nodes.length > 0 ? (
        <div>
          {/* Build tree from nodes and edges */}
          {(() => {
            const nodeMap = new Map();
            const childrenMap = new Map();
            
            // Initialize nodes
            hierarchy.nodes.forEach(node => {
              nodeMap.set(node.id, { ...node, children: [] });
              childrenMap.set(node.id, []);
            });
            
            // Build relationships from edges
            if (hierarchy.edges && hierarchy.edges.length > 0) {
              hierarchy.edges.forEach(edge => {
                if (edge.source && edge.target) {
                  const children = childrenMap.get(edge.source) || [];
                  if (!children.includes(edge.target)) {
                    children.push(edge.target);
                    childrenMap.set(edge.source, children);
                  }
                }
              });
            }
            
            // Find root nodes (no incoming edges)
            const hasParent = new Set();
            hierarchy.edges?.forEach(edge => {
              if (edge.target) hasParent.add(edge.target);
            });
            const roots = hierarchy.nodes.filter(node => !hasParent.has(node.id));
            
            // If no roots, use workflows or all nodes
            const displayNodes = roots.length > 0 ? roots : 
              hierarchy.nodes.filter(n => n.type === 'workflow').length > 0 ?
                hierarchy.nodes.filter(n => n.type === 'workflow') : hierarchy.nodes;
            
            return displayNodes.map(root => {
              const buildNode = (nodeId, level = 0) => {
                const node = nodeMap.get(nodeId);
                if (!node) return null;
                
                const children = childrenMap.get(nodeId) || [];
                const nodeData = {
                  id: node.id,
                  name: node.data?.label || node.label || nodeId,
                  type: node.type,
                  file: node.data?.file,
                  children: children.map(childId => buildNode(childId, level + 1)).filter(Boolean)
                };
                
                return nodeData;
              };
              
              const treeNode = buildNode(root.id);
              return treeNode ? renderTreeNode(treeNode) : null;
            });
          })()}
        </div>
      ) : (
        <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
          <div style={{ fontSize: '48px', marginBottom: '15px' }}>📁</div>
          <h3>No hierarchy data available</h3>
          <p>Upload and parse Informatica XML files to see the repository structure.</p>
          <p style={{ fontSize: '12px', marginTop: '10px', color: '#666' }}>
            <strong>Tip:</strong> Parse workflow files first to build accurate hierarchy relationships.
          </p>
        </div>
      )}

      {hierarchy && hierarchy.standalone && (
        <div style={{ marginTop: '30px', padding: '20px', background: '#f9f9f9', borderRadius: '8px' }}>
          <h3 style={{ marginTop: 0 }}>Standalone Components</h3>
          {hierarchy.standalone.worklets.length > 0 && (
            <div style={{ marginBottom: '15px' }}>
              <h4>Worklets ({hierarchy.standalone.worklets.length})</h4>
              {hierarchy.standalone.worklets.map(wk => (
                <div key={wk.file_id} style={{ marginLeft: '20px', marginBottom: '5px' }}>
                  {getTypeIcon('worklet')} {wk.filename}
                </div>
              ))}
            </div>
          )}
          {hierarchy.standalone.sessions.length > 0 && (
            <div style={{ marginBottom: '15px' }}>
              <h4>Sessions ({hierarchy.standalone.sessions.length})</h4>
              {hierarchy.standalone.sessions.map(sess => (
                <div key={sess.file_id} style={{ marginLeft: '20px', marginBottom: '5px' }}>
                  {getTypeIcon('session')} {sess.filename}
                </div>
              ))}
            </div>
          )}
          {hierarchy.standalone.mappings.length > 0 && (
            <div>
              <h4>Mappings ({hierarchy.standalone.mappings.length})</h4>
              {hierarchy.standalone.mappings.map(map => (
                <div key={map.file_id} style={{ marginLeft: '20px', marginBottom: '5px' }}>
                  {getTypeIcon('mapping')} {map.filename}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

