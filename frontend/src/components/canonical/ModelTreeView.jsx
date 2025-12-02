import React, { useState, useMemo } from 'react';
import apiClient from '../../services/api.js';

/**
 * Hierarchical Tree View for Canonical Model Navigation
 * 
 * Displays workflows → tasks → transformations in a tree structure
 * with expand/collapse functionality and search/filter capabilities.
 * Uses generic canonical model terminology (tasks/transformations) instead of
 * Informatica-specific terms (sessions/mappings).
 */
export default function ModelTreeView({ 
  onSelectMapping, 
  onSelectSession, 
  onSelectWorkflow,
  selectedItem = null 
}) {
  const [workflows, setWorkflows] = useState([]);
  const [expanded, setExpanded] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // 'all', 'workflow', 'task', 'transformation'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load workflows on mount
  React.useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.listWorkflows();
      if (result.success) {
        setWorkflows(result.workflows || []);
        // Expand first workflow by default
        if (result.workflows && result.workflows.length > 0) {
          setExpanded(new Set([result.workflows[0].name]));
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to load workflows');
      console.error('Error loading workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpanded(newExpanded);
  };

  const isExpanded = (id) => expanded.has(id);

  // Filter workflows based on search and filter type
  const filteredWorkflows = useMemo(() => {
    let filtered = workflows;

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(workflow => {
        const matchesWorkflow = workflow.name?.toLowerCase().includes(searchLower);
        const tasks = workflow.tasks || [];
        const matchesTasks = tasks.some(t => 
          t.name?.toLowerCase().includes(searchLower)
        );
        const matchesTransformations = tasks.some(t => {
          const transformations = t.transformations || [];
          return transformations.some(trans => 
            trans.name?.toLowerCase().includes(searchLower) ||
            trans.transformation_name?.toLowerCase().includes(searchLower)
          );
        });
        
        return matchesWorkflow || matchesTasks || matchesTransformations;
      });
    }

    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.map(workflow => {
        const tasks = workflow.tasks || [];
        if (filterType === 'workflow') {
          // Show only workflow, hide tasks/transformations
          return { ...workflow, tasks: [] };
        } else if (filterType === 'task') {
          // Show only tasks, hide transformations
          return {
            ...workflow,
            tasks: tasks.map(t => ({ 
              ...t, 
              transformations: [] 
            }))
          };
        } else if (filterType === 'transformation') {
          // Show only transformations, keep structure
          return workflow;
        }
        return workflow;
      });
    }

    return filtered;
  }, [workflows, searchTerm, filterType]);

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div>Loading workflows...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <div>Error: {error}</div>
        <button onClick={loadWorkflows} style={{ marginTop: '10px' }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Search and Filter Bar */}
      <div style={{ 
        padding: '15px', 
        borderBottom: '1px solid #ddd',
        background: '#f9f9f9'
      }}>
        <div style={{ marginBottom: '10px' }}>
          <input
            type="text"
            placeholder="Search workflows, sessions, mappings..."
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
        <div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{
              width: '100%',
              padding: '6px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '13px'
            }}
          >
            <option value="all">All Types</option>
            <option value="workflow">Workflows</option>
            <option value="task">Tasks</option>
            <option value="transformation">Transformations</option>
          </select>
        </div>
        <div style={{ 
          marginTop: '10px', 
          fontSize: '12px', 
          color: '#666' 
        }}>
          {filteredWorkflows.length} workflow(s) found
        </div>
      </div>

      {/* Tree View */}
      <div style={{ 
        flex: 1, 
        overflow: 'auto', 
        padding: '10px' 
      }}>
        {filteredWorkflows.length === 0 ? (
          <div style={{ 
            padding: '40px', 
            textAlign: 'center', 
            color: '#666' 
          }}>
            No workflows found
          </div>
        ) : (
          filteredWorkflows.map(workflow => (
            <WorkflowNode
              key={workflow.name}
              workflow={workflow}
              expanded={isExpanded(workflow.name)}
              onToggle={() => toggleExpand(workflow.name)}
              onSelectWorkflow={onSelectWorkflow}
              onSelectSession={onSelectSession}
              onSelectMapping={onSelectMapping}
              selectedItem={selectedItem}
              searchTerm={searchTerm}
            />
          ))
        )}
      </div>
    </div>
  );
}

/**
 * Workflow Node Component
 */
function WorkflowNode({ 
  workflow, 
  expanded, 
  onToggle, 
  onSelectWorkflow,
  onSelectSession,
  onSelectMapping,
  selectedItem,
  searchTerm 
}) {
  const [workflowStructure, setWorkflowStructure] = useState(null);
  const [loadingStructure, setLoadingStructure] = useState(false);
  
  const workflowId = `workflow-${workflow.name}`;
  const isSelected = selectedItem?.type === 'workflow' && selectedItem?.name === workflow.name;
  
  // Load workflow structure when expanded
  React.useEffect(() => {
    if (expanded && !workflowStructure && !loadingStructure) {
      loadWorkflowStructure();
    }
  }, [expanded]);
  
  const loadWorkflowStructure = async () => {
    setLoadingStructure(true);
    try {
      const result = await apiClient.getWorkflowStructure(workflow.name);
      if (result.success && result.workflow) {
        setWorkflowStructure(result.workflow);
      }
    } catch (err) {
      console.error('Error loading workflow structure:', err);
    } finally {
      setLoadingStructure(false);
    }
  };
  
  // Use loaded structure if available, otherwise fall back to workflow metadata
  const tasks = workflowStructure?.tasks || workflow.tasks || [];
  const taskCount = workflow.task_count || tasks.length || 0;

  return (
    <div style={{ marginBottom: '5px' }}>
      <div
        onClick={(e) => {
          e.stopPropagation();
          onToggle();
          if (onSelectWorkflow) {
            onSelectWorkflow(workflow);
          }
        }}
        style={{
          padding: '10px',
          background: isSelected ? '#E3F2FD' : 'white',
          border: isSelected ? '2px solid #4A90E2' : '1px solid #ddd',
          borderRadius: '6px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          transition: 'all 0.2s'
        }}
        onMouseEnter={(e) => {
          if (!isSelected) {
            e.currentTarget.style.background = '#f5f5f5';
          }
        }}
        onMouseLeave={(e) => {
          if (!isSelected) {
            e.currentTarget.style.background = 'white';
          }
        }}
      >
        <span style={{ fontSize: '16px' }}>
          {expanded ? '▼' : '▶'}
        </span>
        <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
          {workflow.name}
        </span>
        <span style={{ 
          fontSize: '12px', 
          color: '#666',
          marginLeft: 'auto'
        }}>
          {taskCount} task(s)
        </span>
      </div>

      {expanded && (
        <div style={{ 
          marginLeft: '20px', 
          marginTop: '5px',
          borderLeft: '2px solid #ddd',
          paddingLeft: '10px'
        }}>
          {loadingStructure ? (
            <div style={{ padding: '10px', color: '#666', fontSize: '12px' }}>
              Loading tasks...
            </div>
          ) : tasks.length > 0 ? (
            tasks.map(task => (
              <SessionNode
                key={task.name}
                session={task}
                workflowName={workflow.name}
                onSelectSession={onSelectSession}
                onSelectMapping={onSelectMapping}
                selectedItem={selectedItem}
                searchTerm={searchTerm}
              />
            ))
          ) : (
            <div style={{ padding: '10px', color: '#999', fontSize: '12px' }}>
              No tasks found
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Task Node Component (displays tasks, which are stored as sessions in Neo4j)
 */
function SessionNode({ 
  session, 
  workflowName,
  onSelectSession,
  onSelectMapping,
  selectedItem,
  searchTerm 
}) {
  const [expanded, setExpanded] = useState(false);
  const sessionId = `session-${session.name}`;
  const isSelected = selectedItem?.type === 'session' && selectedItem?.name === session.name;
  // Use generic terminology: transformations (stored as mappings in Neo4j)
  const transformationCount = (session.transformations || session.mappings || [])?.length || 0;

  return (
    <div style={{ marginBottom: '5px' }}>
      <div
        onClick={(e) => {
          e.stopPropagation();
          setExpanded(!expanded);
          if (onSelectSession) {
            onSelectSession(session, workflowName);
          }
        }}
        style={{
          padding: '8px',
          background: isSelected ? '#E8F5E9' : 'white',
          border: isSelected ? '2px solid #4CAF50' : '1px solid #ddd',
          borderRadius: '4px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '13px'
        }}
      >
        <span style={{ fontSize: '12px' }}>
          {expanded ? '▼' : '▶'}
        </span>
        <span style={{ fontWeight: '500' }}>
          {session.name}
        </span>
        <span style={{ 
          fontSize: '11px', 
          color: '#666',
          marginLeft: 'auto'
        }}>
          {transformationCount} transformation(s)
        </span>
      </div>

      {expanded && session.transformations && (
        <div style={{ 
          marginLeft: '20px', 
          marginTop: '5px',
          borderLeft: '2px solid #ddd',
          paddingLeft: '10px'
        }}>
          {(session.transformations || []).map(transformation => (
            <MappingNode
              key={transformation.name}
              mapping={transformation}
              sessionName={session.name}
              workflowName={workflowName}
              onSelectMapping={onSelectMapping}
              selectedItem={selectedItem}
              searchTerm={searchTerm}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Mapping Node Component
 */
function MappingNode({ 
  mapping, 
  sessionName,
  workflowName,
  onSelectMapping,
  selectedItem,
  searchTerm 
}) {
  const mappingId = `mapping-${mapping.name}`;
  const isSelected = selectedItem?.type === 'mapping' && selectedItem?.name === mapping.name;
  const complexity = mapping.complexity || 'UNKNOWN';
  const complexityColor = {
    'LOW': '#4CAF50',
    'MEDIUM': '#FF9800',
    'HIGH': '#F44336',
    'UNKNOWN': '#9E9E9E'
  }[complexity] || '#9E9E9E';

  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
        if (onSelectMapping) {
          onSelectMapping(mapping, sessionName, workflowName);
        }
      }}
      style={{
        padding: '8px',
        background: isSelected ? '#FFF3E0' : 'white',
        border: isSelected ? '2px solid #FF9800' : '1px solid #ddd',
        borderRadius: '4px',
        cursor: 'pointer',
        marginBottom: '4px',
        fontSize: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.background = '#f9f9f9';
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.background = 'white';
        }
      }}
    >
      <span style={{ fontWeight: '500' }}>
        {mapping.mapping_name || mapping.name}
      </span>
      <span style={{ 
        fontSize: '10px', 
        padding: '2px 6px',
        borderRadius: '3px',
        background: complexityColor,
        color: 'white',
        marginLeft: 'auto'
      }}>
        {complexity}
      </span>
    </div>
  );
}

