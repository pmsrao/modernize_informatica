import React, { useState } from 'react';
import ModelTreeView from '../components/canonical/ModelTreeView.jsx';
import apiClient from '../services/api.js';

/**
 * Canonical Model Explorer Page
 * 
 * Provides hierarchical navigation of workflows, sessions, and mappings
 * with detailed views for selected items.
 */
export default function CanonicalModelPage() {
  const [selectedItem, setSelectedItem] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSelectWorkflow = async (workflow) => {
    setSelectedItem({ type: 'workflow', name: workflow.name, data: workflow });
    setDetailData(null);
    setError(null);
    
    // Load workflow details
    setLoading(true);
    try {
      const result = await apiClient.getWorkflowStructure(workflow.name);
      if (result.success) {
        setDetailData(result.workflow);
      } else {
        setError(result.message || 'Failed to load workflow details');
      }
    } catch (err) {
      setError(err.message || 'Failed to load workflow details');
      console.error('Error loading workflow:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSession = async (session, workflowName) => {
    setSelectedItem({ 
      type: 'session', 
      name: session.name, 
      workflowName,
      data: session 
    });
    setDetailData(session);
    setError(null);
  };

  const handleSelectMapping = async (mapping, sessionName, workflowName) => {
    setSelectedItem({ 
      type: 'mapping', 
      name: mapping.name,
      mappingName: mapping.mapping_name,
      sessionName,
      workflowName,
      data: mapping 
    });
    setDetailData(null);
    setError(null);
    
    // Load mapping structure/details
    setLoading(true);
    try {
      const mappingName = mapping.mapping_name || mapping.name;
      const result = await apiClient.getMappingStructure(mappingName);
      if (result.success) {
        setDetailData({
          ...mapping,
          structure: result.graph,
          ...result
        });
      } else {
        // Fallback: just use the mapping data we have
        setDetailData(mapping);
      }
    } catch (err) {
      // Fallback: just use the mapping data we have
      setDetailData(mapping);
      console.error('Error loading mapping structure:', err);
    } finally {
      setLoading(false);
    }
  };

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
        <h1 style={{ margin: 0, color: '#333' }}>Canonical Model</h1>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          Navigate: Workflow → Task(s) → Transformation(s). Start by selecting a workflow.
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
        {/* Tree View Sidebar */}
        <div style={{ 
          width: '350px', 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          overflow: 'hidden',
          background: 'white',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <ModelTreeView
            onSelectMapping={handleSelectMapping}
            onSelectSession={handleSelectSession}
            onSelectWorkflow={handleSelectWorkflow}
            selectedItem={selectedItem}
          />
        </div>

        {/* Detail View */}
        <div style={{ 
          flex: 1, 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          overflow: 'auto',
          background: 'white',
          padding: '20px'
        }}>
          {!selectedItem ? (
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
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
              <h2 style={{ margin: '10px 0', color: '#333' }}>Select an Item to View Details</h2>
              <p style={{ margin: '5px 0', color: '#666' }}>
                Choose a workflow, task, or transformation from the tree view to see detailed information
              </p>
            </div>
          ) : loading ? (
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
                <div>Loading details...</div>
              </div>
            </div>
          ) : error ? (
            <div style={{ 
              padding: '20px', 
              background: '#ffebee',
              border: '1px solid #f44336',
              borderRadius: '4px',
              color: '#c62828'
            }}>
              <strong>Error:</strong> {error}
            </div>
          ) : (
            <DetailView 
              item={selectedItem} 
              data={detailData || selectedItem.data}
            />
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Detail View Component
 * Shows detailed information based on selected item type
 */
function DetailView({ item, data }) {
  if (item.type === 'workflow') {
    return <WorkflowDetailView workflow={data} />;
  } else if (item.type === 'session') {
    return <SessionDetailView session={data} workflowName={item.workflowName} />;
  } else if (item.type === 'mapping') {
    return <MappingDetailView mapping={data} sessionName={item.sessionName} workflowName={item.workflowName} />;
  }
  
  return <div>Unknown item type: {item.type}</div>;
}

/**
 * Workflow Detail View
 */
function WorkflowDetailView({ workflow }) {
  // Support both generic terminology (tasks) and Informatica terminology (sessions)
  const tasks = workflow?.tasks || workflow?.sessions || [];
  
  return (
    <div>
      <div style={{ marginBottom: '30px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#333' }}>
          {workflow?.name || 'Unknown Workflow'}
        </h2>
        <div style={{ fontSize: '14px', color: '#666' }}>
          Workflow Details
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 10px 0', color: '#555' }}>Overview</h3>
        <div style={{ 
          background: '#f5f5f5', 
          padding: '15px', 
          borderRadius: '6px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '15px'
        }}>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Type</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {workflow?.type || 'N/A'}
            </div>
          </div>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Tasks</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {tasks.length}
            </div>
          </div>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Total Transformations</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {tasks.reduce((sum, t) => sum + ((t.transformations || t.mappings || []).length), 0)}
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Tasks</h3>
        {tasks.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            No tasks found
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {tasks.map((task, idx) => {
              // Support both generic terminology (transformations) and Informatica terminology (mappings)
              const transformations = task.transformations || task.mappings || [];
              return (
                <div
                  key={task.name || idx}
                  style={{
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    padding: '15px',
                    background: '#fafafa',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onClick={() => handleSelectSession(task, workflow.name)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#f0f0f0';
                    e.currentTarget.style.borderColor = '#4A90E2';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#fafafa';
                    e.currentTarget.style.borderColor = '#ddd';
                  }}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '14px' }}>
                    {task.name}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    <div>Type: {task.type || 'N/A'}</div>
                    <div>Transformations: {transformations.length}</div>
                  </div>
                  {transformations.length > 0 && (
                    <div style={{ marginTop: '10px', fontSize: '12px' }}>
                      <strong>Transformations:</strong>
                      <ul style={{ margin: '5px 0 0 20px', padding: 0 }}>
                        {transformations.map((t, i) => (
                          <li key={i} style={{ marginBottom: '3px' }}>
                            {t.transformation_name || t.mapping_name || t.name} 
                            {t.complexity && (
                              <span style={{ 
                                marginLeft: '8px',
                                padding: '2px 6px',
                                borderRadius: '3px',
                                background: t.complexity === 'LOW' ? '#4CAF50' : 
                                           t.complexity === 'MEDIUM' ? '#FF9800' : '#F44336',
                                color: 'white',
                                fontSize: '10px'
                              }}>
                                {t.complexity}
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Session Detail View
 */
function SessionDetailView({ session, workflowName }) {
  const mappings = session?.mappings || [];
  
  return (
    <div>
      <div style={{ marginBottom: '30px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#333' }}>
          {session?.name || 'Unknown Task'}
        </h2>
        <div style={{ fontSize: '14px', color: '#666' }}>
          Task in workflow: <strong>{workflowName}</strong>
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 10px 0', color: '#555' }}>Overview</h3>
        <div style={{ 
          background: '#f5f5f5', 
          padding: '15px', 
          borderRadius: '6px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '15px'
        }}>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Type</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {session?.type || 'N/A'}
            </div>
          </div>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Transformations</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {mappings.length}
            </div>
          </div>
        </div>
      </div>

      {session?.properties && Object.keys(session.properties).length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#555' }}>Properties</h3>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '15px', 
            borderRadius: '6px',
            fontSize: '13px'
          }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(session.properties, null, 2)}
            </pre>
          </div>
        </div>
      )}

      <div>
        <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Transformations</h3>
        {mappings.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            No transformations found
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {mappings.map((mapping, idx) => (
              <div
                key={mapping.name || idx}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  padding: '15px',
                  background: '#fafafa',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#f0f0f0';
                  e.currentTarget.style.borderColor = '#4A90E2';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#fafafa';
                  e.currentTarget.style.borderColor = '#ddd';
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '14px' }}>
                  {mapping.mapping_name || mapping.name}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  {mapping.complexity && (
                    <span style={{ 
                      marginRight: '10px',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      background: mapping.complexity === 'LOW' ? '#4CAF50' : 
                                 mapping.complexity === 'MEDIUM' ? '#FF9800' : '#F44336',
                      color: 'white'
                    }}>
                      {mapping.complexity}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Mapping Detail View - Shows Transformations
 */
function MappingDetailView({ mapping, sessionName, workflowName }) {
  const structure = mapping?.structure;
  const complexity = mapping?.complexity || mapping?.data?.complexity;
  const transformations = structure?.nodes?.filter(n => n.type === 'transformation') || [];
  const sources = structure?.nodes?.filter(n => n.type === 'source') || [];
  const targets = structure?.nodes?.filter(n => n.type === 'target') || [];
  
  return (
    <div>
      <div style={{ marginBottom: '30px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#333' }}>
          {mapping?.transformation_name || mapping?.mapping_name || mapping?.name || 'Unknown Transformation'}
        </h2>
        <div style={{ fontSize: '14px', color: '#666' }}>
          <div>Workflow: <strong>{workflowName}</strong> → Task: <strong>{sessionName}</strong></div>
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 10px 0', color: '#555' }}>Overview</h3>
        <div style={{ 
          background: '#f5f5f5', 
          padding: '15px', 
          borderRadius: '6px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '15px'
        }}>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Complexity</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {complexity ? (
                <span style={{ 
                  padding: '4px 8px',
                  borderRadius: '4px',
                  background: complexity === 'LOW' ? '#4CAF50' : 
                             complexity === 'MEDIUM' ? '#FF9800' : '#F44336',
                  color: 'white',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}>
                  {complexity}
                </span>
              ) : 'N/A'}
            </div>
          </div>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Sources</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {sources.length}
            </div>
          </div>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Targets</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {targets.length}
            </div>
          </div>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Transformations</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {transformations.length}
            </div>
          </div>
        </div>
      </div>

      {/* Transformations Section - The Heart of Canonical Model */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Transformations</h3>
        {transformations.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666', background: '#f5f5f5', borderRadius: '6px' }}>
            No transformations found
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {transformations.map((trans, idx) => (
              <div
                key={trans.id || idx}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  padding: '15px',
                  background: '#fafafa'
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '14px', color: '#333' }}>
                  {trans.label || trans.data?.name || `Transformation ${idx + 1}`}
                </div>
                {trans.data && (
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {trans.data.type && (
                      <div><strong>Type:</strong> {trans.data.type}</div>
                    )}
                    {trans.data.transformation_type && (
                      <div><strong>Transformation Type:</strong> {trans.data.transformation_type}</div>
                    )}
                    {trans.data.description && (
                      <div style={{ marginTop: '5px' }}><strong>Description:</strong> {trans.data.description}</div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Sources</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {sources.map((source, idx) => (
              <div
                key={source.id || idx}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  padding: '12px',
                  background: '#f0f8ff'
                }}
              >
                <div style={{ fontWeight: 'bold', fontSize: '13px' }}>
                  {source.label || source.data?.name || `Source ${idx + 1}`}
                </div>
                {source.data?.table && (
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                    Table: {source.data.table.name || source.data.table}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Targets */}
      {targets.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Targets</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {targets.map((target, idx) => (
              <div
                key={target.id || idx}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  padding: '12px',
                  background: '#f0fff0'
                }}
              >
                <div style={{ fontWeight: 'bold', fontSize: '13px' }}>
                  {target.label || target.data?.name || `Target ${idx + 1}`}
                </div>
                {target.data?.table && (
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                    Table: {target.data.table.name || target.data.table}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

