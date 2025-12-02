import React, { useState, useEffect } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  MarkerType,
  Handle,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import apiClient from '../services/api.js';
import RepositoryStructurePage from './RepositoryStructurePage.jsx';

/**
 * Simple Tree View Component
 * Displays hierarchy in an easy-to-read indented tree format
 * 
 * Note: In Informatica, the same mapping can be reused across multiple workflows/worklets/sessions.
 * This is a valid pattern - mappings are reusable components. Duplicate mapping names in the tree
 * indicate that the same mapping is used in different contexts, which is expected behavior.
 */
const SimpleTreeView = ({ nodes, edges, onFileAction, onParseAndEnhance }) => {
  // Build tree structure from nodes and edges
  const buildTree = () => {
    console.log('Building tree view:', { nodesCount: nodes.length, edgesCount: edges.length });
    console.log('Nodes:', nodes.map(n => ({ id: n.id, type: n.type, label: n.data?.label })));
    console.log('Edges:', edges.map(e => ({ source: e.source, target: e.target })));
    
    const nodeMap = new Map();
    const childrenMap = new Map();
    
    // Initialize all nodes
    nodes.forEach(node => {
      nodeMap.set(node.id, node);
      childrenMap.set(node.id, []);
    });
    
    // Build parent-child relationships from edges
    if (edges.length > 0) {
      edges.forEach(edge => {
        if (edge.source && edge.target) {
          const children = childrenMap.get(edge.source) || [];
          if (!children.includes(edge.target)) {
            children.push(edge.target);
            childrenMap.set(edge.source, children);
          }
        }
      });
    } else {
      // Fallback: Build hierarchy based on type order if no edges
      // Workflow -> Worklet -> Session -> Mapping
      const typeOrder = { workflow: 0, worklet: 1, session: 2, mapping: 3 };
      const nodesByType = {};
      nodes.forEach(node => {
        const type = node.type;
        if (!nodesByType[type]) nodesByType[type] = [];
        nodesByType[type].push(node);
      });
      
      // Link workflows to worklets, worklets to sessions, sessions to mappings
      nodesByType.workflow?.forEach(workflow => {
        nodesByType.worklet?.forEach(worklet => {
          childrenMap.get(workflow.id).push(worklet.id);
        });
      });
      nodesByType.worklet?.forEach(worklet => {
        nodesByType.session?.forEach(session => {
          childrenMap.get(worklet.id).push(session.id);
        });
      });
      nodesByType.session?.forEach(session => {
        nodesByType.mapping?.forEach(mapping => {
          childrenMap.get(session.id).push(mapping.id);
        });
      });
    }
    
    // Find root nodes (nodes with no incoming edges)
    const hasParent = new Set();
    edges.forEach(edge => {
      if (edge.target) hasParent.add(edge.target);
    });
    // Also check childrenMap for fallback hierarchy
    childrenMap.forEach((children, parentId) => {
      children.forEach(childId => hasParent.add(childId));
    });
    
    const roots = nodes.filter(node => !hasParent.has(node.id));
    
    // If no roots found, use workflows as roots, or all nodes if no workflows
    const finalRoots = roots.length > 0 ? roots : 
      (nodes.filter(n => n.type === 'workflow').length > 0 ? 
        nodes.filter(n => n.type === 'workflow') : nodes);
    
    console.log('Tree roots:', finalRoots.map(r => ({ id: r.id, type: r.type, label: r.data?.label })));
    
    // Render tree recursively
    const renderNode = (nodeId, level = 0) => {
      const node = nodeMap.get(nodeId);
      if (!node) return null;
      
      const children = childrenMap.get(nodeId) || [];
      const indent = level * 30;
      const typeColors = {
        workflow: '#4A90E2',
        worklet: '#9B59B6',
        session: '#FFA500',
        mapping: '#50C878'
      };
      const typeIcons = {
        workflow: '🔄',
        worklet: '📦',
        session: '⚙️',
        mapping: '📋'
      };
      const color = typeColors[node.type] || '#95A5A6';
      const icon = typeIcons[node.type] || '📄';
      
      return (
        <div key={nodeId} style={{ marginBottom: '6px' }}>
          <div style={{
            marginLeft: `${indent}px`,
            padding: level === 0 ? '12px 15px' : '8px 12px',
            background: level === 0 ? color : level % 2 === 0 ? '#fafafa' : 'white',
            color: level === 0 ? 'white' : '#333',
            borderRadius: '6px',
            border: `1px solid ${level === 0 ? color : '#e0e0e0'}`,
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontWeight: level === 0 ? 'bold' : 'normal',
            fontSize: level === 0 ? '15px' : '14px',
            transition: 'all 0.2s',
            cursor: 'pointer'
          }}
          onMouseEnter={(e) => {
            if (level > 0) {
              e.currentTarget.style.background = '#f0f0f0';
              e.currentTarget.style.borderColor = color;
            }
          }}
          onMouseLeave={(e) => {
            if (level > 0) {
              e.currentTarget.style.background = level % 2 === 0 ? '#fafafa' : 'white';
              e.currentTarget.style.borderColor = '#e0e0e0';
            }
          }}
          >
            <span style={{ fontSize: level === 0 ? '20px' : '18px' }}>{icon}</span>
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {node.data.label || nodeId}
            </span>
            <span style={{
              fontSize: '10px',
              padding: '4px 8px',
              background: level === 0 ? 'rgba(255,255,255,0.25)' : color,
              color: 'white',
              borderRadius: '4px',
              fontWeight: 'bold',
              whiteSpace: 'nowrap'
            }}>
              {node.type.toUpperCase()}
            </span>
          </div>
          {children.map(childId => renderNode(childId, level + 1))}
        </div>
      );
    };
    
    return (
      <div>
        {finalRoots.map(root => renderNode(root.id))}
      </div>
    );
  };
  
  const treeResult = buildTree();
  
  // Add debug info if no hierarchy visible
  if (nodes.length > 0 && edges.length === 0) {
    return (
      <div>
        <div style={{ 
          padding: '10px', 
          background: '#fff3cd', 
          borderRadius: '6px', 
          marginBottom: '15px',
          fontSize: '13px',
          color: '#856404'
        }}>
          ⚠️ <strong>Note:</strong> No explicit relationships found. Showing hierarchy based on component types (Workflow → Worklet → Session → Mapping).
        </div>
        {treeResult}
      </div>
    );
  }
  
  return treeResult;
};

/**
 * Repository View Page
 * 
 * Provides an appealing visual representation of uploaded Informatica files
 * organized by type (Workflow, Worklet, Session, Mapping) with interactive
 * graph visualization showing relationships.
 */
export default function RepositoryViewPage({ files, onFileAction, onParseAndEnhance, onBackClick }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [hierarchyGraph, setHierarchyGraph] = useState(null);
  const [viewMode, setViewMode] = useState('cards'); // 'cards', 'graph', 'structure', or 'tree'
  const [loading, setLoading] = useState(false);
  const [bulkParsing, setBulkParsing] = useState(false);
  const [bulkParseProgress, setBulkParseProgress] = useState({ current: 0, total: 0, errors: [] });

  useEffect(() => {
    if (viewMode === 'graph' && files.length > 0) {
      loadHierarchyGraph();
    }
  }, [viewMode, files]);

  const loadHierarchyGraph = async () => {
    setLoading(true);
    try {
      const result = await apiClient.getHierarchy();
      if (result.success && result.hierarchy) {
        const graphData = result.hierarchy;
        
        const nodes = graphData.nodes.map((node) => ({
          id: node.id,
          type: node.type,
          data: { ...node.data, label: node.label },
          position: { x: 0, y: 0 }
        }));

        const edges = graphData.edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: 'smoothstep',
          animated: true,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 25,
            height: 25,
            color: '#4A90E2'
          },
          style: { 
            stroke: '#4A90E2', 
            strokeWidth: 3,
            opacity: 0.8
          },
          label: edge.label || '',
          labelStyle: {
            fill: '#4A90E2',
            fontWeight: 600,
            fontSize: '11px'
          },
          labelBgStyle: {
            fill: 'white',
            fillOpacity: 0.8
          }
        }));

        layoutNodes(nodes, edges);
        setHierarchyGraph({ nodes, edges });
      }
    } catch (err) {
      console.error('Error loading hierarchy:', err);
    } finally {
      setLoading(false);
    }
  };

  const layoutNodes = (nodes, edges) => {
    const levels = { workflow: 0, worklet: 1, session: 2, mapping: 3 };
    const nodesByType = { workflow: [], worklet: [], session: [], mapping: [] };

    nodes.forEach(node => {
      const type = node.type;
      if (nodesByType[type]) {
        nodesByType[type].push(node);
      }
    });

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
        <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.9 }}>Workflow</div>
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
        <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.9 }}>Worklet</div>
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
        <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.9 }}>Session</div>
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
        <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.9 }}>Mapping</div>
      </div>
    )
  };

  const getFileTypeIcon = (type) => {
    const icons = {
      'mapping': '📋',
      'workflow': '🔄',
      'session': '⚙️',
      'worklet': '📦',
      'unknown': '📄'
    };
    return icons[type] || icons.unknown;
  };

  const getFileTypeColor = (type) => {
    const colors = {
      'mapping': '#4A90E2',
      'workflow': '#50C878',
      'session': '#FFA500',
      'worklet': '#9B59B6',
      'unknown': '#95A5A6'
    };
    return colors[type] || colors.unknown;
  };

  const workflows = files.filter(f => f.file_type === 'workflow');
  const worklets = files.filter(f => f.file_type === 'worklet');
  const sessions = files.filter(f => f.file_type === 'session');
  const mappings = files.filter(f => f.file_type === 'mapping');

  // Debug: Log file counts
  useEffect(() => {
    console.log('Repository View - File counts:', {
      total: files.length,
      workflows: workflows.length,
      worklets: worklets.length,
      sessions: sessions.length,
      mappings: mappings.length,
      allFiles: files.map(f => ({ name: f.filename, type: f.file_type }))
    });
  }, [files]);

  // Compact file list item (no boxes)
  const FileListItem = ({ file }) => (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '10px 12px',
        borderBottom: '1px solid #E0E0E0',
        cursor: 'pointer',
        background: selectedFile?.file_id === file.file_id ? '#E3F2FD' : 'white',
        transition: 'background 0.2s',
      }}
      onClick={() => setSelectedFile(file)}
      onMouseEnter={(e) => {
        if (selectedFile?.file_id !== file.file_id) {
          e.currentTarget.style.background = '#F5F5F5';
        }
      }}
      onMouseLeave={(e) => {
        if (selectedFile?.file_id !== file.file_id) {
          e.currentTarget.style.background = 'white';
        }
      }}
    >
      <span style={{ fontSize: '20px', marginRight: '12px', minWidth: '24px' }}>
        {getFileTypeIcon(file.file_type)}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ 
          fontWeight: '500', 
          fontSize: '14px', 
          color: '#212121',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {file.filename}
        </div>
      </div>
      <div style={{
        display: 'inline-block',
        padding: '3px 8px',
        background: getFileTypeColor(file.file_type),
        color: 'white',
        borderRadius: '4px',
        fontSize: '11px',
        fontWeight: '600',
        marginRight: '12px',
        whiteSpace: 'nowrap'
      }}>
        {file.file_type.toUpperCase()}
      </div>
      {selectedFile?.file_id === file.file_id && (
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onParseAndEnhance && onParseAndEnhance(file.file_id);
            }}
            style={{
              padding: '6px 12px',
              background: '#4A90E2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: '500',
              fontSize: '12px'
            }}
          >
            Parse
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onFileAction && onFileAction(file);
            }}
            style={{
              padding: '6px 12px',
              background: '#50C878',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: '500',
              fontSize: '12px'
            }}
          >
            View
          </button>
        </div>
      )}
    </div>
  );

  const handleBulkParse = async () => {
    // Filter to only mappings (they create canonical models)
    const mappingFiles = files.filter(f => f.file_type === 'mapping');
    
    if (mappingFiles.length === 0) {
      alert('No mapping files found to parse. Please upload mapping XML files first.');
      return;
    }

      if (!confirm(`Parse and enhance ${mappingFiles.length} mapping file(s) with AI and save to canonical model?\n\nThis will:\n- Parse each mapping file\n- Enhance with AI agents (risk detection, optimization suggestions)\n- Save to the canonical model (Neo4j graph database)`)) {
        return;
      }

    setBulkParsing(true);
    setBulkParseProgress({ current: 0, total: mappingFiles.length, errors: [] });
    const errors = [];

    for (let i = 0; i < mappingFiles.length; i++) {
      const file = mappingFiles[i];
      setBulkParseProgress({ 
        current: i + 1, 
        total: mappingFiles.length, 
        errors: [...errors] 
      });

      try {
        const result = await onParseAndEnhance(file.file_id);
        // Check if parsing actually succeeded
        if (!result || !result.success) {
          errors.push({ 
            file: file.filename, 
            error: result?.message || result?.errors?.join(', ') || 'Parse returned unsuccessful result' 
          });
        }
        // Small delay to avoid overwhelming the API
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (err) {
        errors.push({ file: file.filename, error: err.message || err.detail || 'Parse failed' });
        setBulkParseProgress({ 
          current: i + 1, 
          total: mappingFiles.length, 
          errors: [...errors] 
        });
      }
    }

    setBulkParsing(false);
    
    // Reload mappings to get accurate count
    try {
      const mappingsResult = await apiClient.listMappings();
      const actualCount = mappingsResult.mappings?.length || 0;
      const expectedCount = mappingFiles.length;
      
      if (errors.length > 0) {
        alert(`Bulk parse completed with ${errors.length} error(s).\n\nExpected: ${expectedCount} mappings\nCreated: ${actualCount} mappings\n\nErrors:\n${errors.map(e => `- ${e.file}: ${e.error}`).join('\n')}`);
      } else if (actualCount < expectedCount) {
        alert(`Bulk parse completed, but only ${actualCount} out of ${expectedCount} mappings were created. Some mappings may have failed silently.`);
      } else {
        alert(`Successfully parsed and enhanced ${actualCount} mapping file(s)!`);
      }
    } catch (err) {
      if (errors.length > 0) {
        alert(`Bulk parse completed with ${errors.length} error(s).\n\nErrors:\n${errors.map(e => `- ${e.file}: ${e.error}`).join('\n')}`);
      } else {
        alert(`Bulk parse completed. ${mappingFiles.length} file(s) processed.`);
      }
    }
  };


  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#f5f5f5' }}>
      {/* Single Action Bar - All buttons in one row, Back button aligned right */}
      <div style={{ 
        padding: '12px 20px', 
        background: 'white', 
        borderBottom: '1px solid #e0e0e0',
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap'
      }}>
        {/* Left side: Action Buttons and View Mode */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Action Buttons */}
          {files.filter(f => f.file_type === 'mapping').length > 0 && (
            <>
              <button
                onClick={handleBulkParse}
                disabled={bulkParsing}
                style={{
                  padding: '8px 16px',
                  background: bulkParsing ? '#ccc' : '#50C878',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: bulkParsing ? 'not-allowed' : 'pointer',
                  fontWeight: '600',
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  whiteSpace: 'nowrap'
                }}
              >
                {bulkParsing ? (
                  <>
                    <span>⏳</span>
                    <span>Parsing... ({bulkParseProgress.current}/{bulkParseProgress.total})</span>
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    <span>Parse All Mappings</span>
                  </>
                )}
              </button>
            </>
          )}
          
          {/* Divider */}
          {files.filter(f => f.file_type === 'mapping').length > 0 && (
            <div style={{ 
              width: '1px', 
              height: '24px', 
              background: '#E0E0E0',
              margin: '0 4px'
            }} />
          )}
          
          {/* View Mode Toggle */}
          <span style={{ fontSize: '13px', color: '#666', marginRight: '4px' }}>View:</span>
          <button
            onClick={() => setViewMode('cards')}
            style={{
              padding: '8px 16px',
              background: viewMode === 'cards' ? '#4A90E2' : '#f5f5f5',
              color: viewMode === 'cards' ? 'white' : '#333',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: viewMode === 'cards' ? '600' : 'normal',
              fontSize: '13px',
              whiteSpace: 'nowrap'
            }}
          >
            📋 Cards
          </button>
          <button
            onClick={() => setViewMode('structure')}
            style={{
              padding: '8px 16px',
              background: viewMode === 'structure' ? '#4A90E2' : '#f5f5f5',
              color: viewMode === 'structure' ? 'white' : '#333',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: viewMode === 'structure' ? '600' : 'normal',
              fontSize: '13px',
              whiteSpace: 'nowrap'
            }}
          >
            🌳 Structure
          </button>
          <button
            onClick={() => setViewMode('graph')}
            style={{
              padding: '8px 16px',
              background: viewMode === 'graph' ? '#4A90E2' : '#f5f5f5',
              color: viewMode === 'graph' ? 'white' : '#333',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: viewMode === 'graph' ? '600' : 'normal',
              fontSize: '13px',
              whiteSpace: 'nowrap'
            }}
          >
            🕸️ Graph
          </button>
          <button
            onClick={() => setViewMode('tree')}
            style={{
              padding: '8px 16px',
              background: viewMode === 'tree' ? '#4A90E2' : '#f5f5f5',
              color: viewMode === 'tree' ? 'white' : '#333',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: viewMode === 'tree' ? '600' : 'normal',
              fontSize: '13px',
              whiteSpace: 'nowrap'
            }}
            title="Simple tree view - easiest to read"
          >
            🌲 Tree
          </button>
        </div>

        {/* Right side: Back Button */}
        {onBackClick && (
          <button
            onClick={onBackClick}
            style={{
              padding: '8px 16px',
              background: '#757575',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              whiteSpace: 'nowrap',
              marginLeft: 'auto'
            }}
          >
            <span>←</span>
            <span>Back</span>
          </button>
        )}
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
        {viewMode === 'cards' ? (
          <div style={{ background: 'white', borderRadius: '8px', overflow: 'hidden' }}>
            {/* Workflows Section */}
            {workflows.length > 0 && (
              <div>
                <div style={{ 
                  padding: '12px 16px',
                  background: '#E8F5E9',
                  borderBottom: '1px solid #C8E6C9',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span style={{ fontSize: '18px' }}>🔄</span>
                  <span style={{ fontWeight: '600', fontSize: '14px', color: '#50C878' }}>
                    Workflows ({workflows.length})
                  </span>
                </div>
                {workflows.map(wf => (
                  <FileListItem key={wf.file_id} file={wf} />
                ))}
              </div>
            )}

            {/* Worklets Section */}
            {worklets.length > 0 && (
              <div>
                <div style={{ 
                  padding: '12px 16px',
                  background: '#F3E5F5',
                  borderBottom: '1px solid #E1BEE7',
                  borderTop: workflows.length > 0 ? '1px solid #E1BEE7' : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span style={{ fontSize: '18px' }}>📦</span>
                  <span style={{ fontWeight: '600', fontSize: '14px', color: '#9B59B6' }}>
                    Worklets ({worklets.length})
                  </span>
                </div>
                {worklets.map(wk => (
                  <FileListItem key={wk.file_id} file={wk} />
                ))}
              </div>
            )}

            {/* Sessions Section */}
            {sessions.length > 0 && (
              <div>
                <div style={{ 
                  padding: '12px 16px',
                  background: '#FFF3E0',
                  borderBottom: '1px solid #FFE0B2',
                  borderTop: (workflows.length > 0 || worklets.length > 0) ? '1px solid #FFE0B2' : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span style={{ fontSize: '18px' }}>⚙️</span>
                  <span style={{ fontWeight: '600', fontSize: '14px', color: '#FFA500' }}>
                    Sessions ({sessions.length})
                  </span>
                </div>
                {sessions.map(sess => (
                  <FileListItem key={sess.file_id} file={sess} />
                ))}
              </div>
            )}

            {/* Mappings Section */}
            {mappings.length > 0 && (
              <div>
                <div style={{ 
                  padding: '12px 16px',
                  background: '#E3F2FD',
                  borderBottom: '1px solid #BBDEFB',
                  borderTop: (workflows.length > 0 || worklets.length > 0 || sessions.length > 0) ? '1px solid #BBDEFB' : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span style={{ fontSize: '18px' }}>📋</span>
                  <span style={{ fontWeight: '600', fontSize: '14px', color: '#4A90E2' }}>
                    Mappings ({mappings.length})
                  </span>
                </div>
                {mappings.map(map => (
                  <FileListItem key={map.file_id} file={map} />
                ))}
              </div>
            )}

            {files.length === 0 && (
              <div style={{
                padding: '60px',
                textAlign: 'center',
                color: '#999'
              }}>
                <div style={{ fontSize: '64px', marginBottom: '20px' }}>📁</div>
                <h3>No files uploaded yet</h3>
                <p>Upload Informatica XML files to see them here</p>
              </div>
            )}
          </div>
        ) : viewMode === 'structure' ? (
          <RepositoryStructurePage
            files={files}
            onFileAction={onFileAction}
            onParseAndEnhance={onParseAndEnhance}
          />
        ) : viewMode === 'tree' ? (
          <div style={{ 
            background: 'white', 
            borderRadius: '8px', 
            padding: '20px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            minHeight: '100%'
          }}>
            {hierarchyGraph && hierarchyGraph.nodes.length > 0 ? (
              <SimpleTreeView 
                nodes={hierarchyGraph.nodes} 
                edges={hierarchyGraph.edges}
                onFileAction={onFileAction}
                onParseAndEnhance={onParseAndEnhance}
              />
            ) : (
              <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                <div style={{ fontSize: '48px', marginBottom: '15px' }}>🌲</div>
                <h3>No hierarchy data available</h3>
                <p>Parse workflow files to see the hierarchy tree</p>
              </div>
            )}
          </div>
        ) : (
          <div style={{ flex: 1, border: '1px solid #ddd', borderRadius: '8px', background: 'white', position: 'relative' }}>
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center' }}>Loading graph...</div>
          ) : hierarchyGraph && hierarchyGraph.nodes.length > 0 ? (
            <>
              <div style={{
                position: 'absolute',
                top: '10px',
                left: '10px',
                zIndex: 10,
                background: 'white',
                padding: '15px',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                fontSize: '12px',
                maxWidth: '300px',
                border: '2px solid #4A90E2'
              }}>
                <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '14px', color: '#4A90E2' }}>📖 How to Read This Graph:</div>
                <div style={{ marginBottom: '8px', lineHeight: '1.6' }}>
                  <div><strong>Flow Direction:</strong> Left → Right</div>
                  <div style={{ marginTop: '5px' }}>
                    <span style={{ color: '#4A90E2' }}>🔄 Workflow</span> → 
                    <span style={{ color: '#9B59B6' }}> 📦 Worklet</span> → 
                    <span style={{ color: '#FFA500' }}> ⚙️ Session</span> → 
                    <span style={{ color: '#50C878' }}> 📋 Mapping</span>
                  </div>
                </div>
                <div style={{ fontSize: '11px', color: '#666', fontStyle: 'italic' }}>
                  Arrows show parent-child relationships. Click and drag to explore.
                </div>
              </div>
              <ReactFlow
                nodes={hierarchyGraph.nodes}
                edges={hierarchyGraph.edges}
                nodeTypes={nodeTypes}
                fitView
                style={{ background: '#fafafa' }}
              >
                <Background />
                <Controls />
                <MiniMap />
              </ReactFlow>
            </>
          ) : (
            <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
              <div style={{ fontSize: '48px', marginBottom: '15px' }}>🕸️</div>
              <h3>No hierarchy data available</h3>
              <p>Parse workflow files to see the hierarchy graph</p>
            </div>
          )}
          </div>
        )}
      </div>
    </div>
  );
}

