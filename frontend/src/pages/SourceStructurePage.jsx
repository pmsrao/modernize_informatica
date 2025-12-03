import React, { useState } from 'react';
import ModelTreeView from '../components/canonical/ModelTreeView.jsx';
import apiClient from '../services/api.js';

/**
 * Source Structure Page
 * 
 * Displays hierarchical view of workflows, sessions, and mappings
 * using the ModelTreeView component.
 */
export default function SourceStructurePage() {
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
      const result = await apiClient.getPipelineStructure(workflow.name);
      if (result.success) {
        setDetailData(result.pipeline);
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
        <h1 style={{ margin: 0, color: '#333' }}>Source Structure</h1>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          Hierarchical view of workflows, sessions, and mappings from Neo4j
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
          width: '400px', 
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
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>🌳</div>
              <h2 style={{ margin: '10px 0', color: '#333' }}>Select an Item to View Details</h2>
              <p style={{ margin: '5px 0', color: '#666' }}>
                Choose a workflow, session, or mapping from the tree view to see detailed information
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
  const sessions = workflow?.sessions || [];
  
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
            <strong style={{ color: '#666', fontSize: '12px' }}>Sessions</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {sessions.length}
            </div>
          </div>
          <div>
            <strong style={{ color: '#666', fontSize: '12px' }}>Total Mappings</strong>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {sessions.reduce((sum, s) => sum + (s.mappings?.length || 0), 0)}
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Sessions</h3>
        {sessions.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            No sessions found
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {sessions.map((session, idx) => (
              <div
                key={session.name || idx}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  padding: '15px',
                  background: '#fafafa'
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '14px' }}>
                  {session.name}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  <div>Type: {session.type || 'N/A'}</div>
                  <div>Mappings: {session.mappings?.length || 0}</div>
                </div>
                {session.mappings && session.mappings.length > 0 && (
                  <div style={{ marginTop: '10px', fontSize: '12px' }}>
                    <strong>Mappings:</strong>
                    <ul style={{ margin: '5px 0 0 20px', padding: 0 }}>
                      {session.mappings.map((m, i) => (
                        <li key={i} style={{ marginBottom: '3px' }}>
                          {m.mapping_name || m.name} 
                          {m.complexity && (
                            <span style={{ 
                              marginLeft: '8px',
                              padding: '2px 6px',
                              borderRadius: '3px',
                              background: m.complexity === 'LOW' ? '#4CAF50' : 
                                         m.complexity === 'MEDIUM' ? '#FF9800' : '#F44336',
                              color: 'white',
                              fontSize: '10px'
                            }}>
                              {m.complexity}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
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
          {session?.name || 'Unknown Session'}
        </h2>
        <div style={{ fontSize: '14px', color: '#666' }}>
          Session in workflow: <strong>{workflowName}</strong>
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
            <strong style={{ color: '#666', fontSize: '12px' }}>Mappings</strong>
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
        <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Mappings</h3>
        {mappings.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            No mappings found
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
                  background: '#fafafa'
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
 * Mapping Detail View
 */
function MappingDetailView({ mapping, sessionName, workflowName }) {
  const structure = mapping?.structure;
  const complexity = mapping?.complexity || mapping?.data?.complexity;
  
  return (
    <div>
      <div style={{ marginBottom: '30px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#333' }}>
          {mapping?.mapping_name || mapping?.name || 'Unknown Mapping'}
        </h2>
        <div style={{ fontSize: '14px', color: '#666' }}>
          <div>Workflow: <strong>{workflowName}</strong></div>
          <div>Session: <strong>{sessionName}</strong></div>
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
          {mapping?.source_count !== undefined && (
            <div>
              <strong style={{ color: '#666', fontSize: '12px' }}>Sources</strong>
              <div style={{ fontSize: '14px', marginTop: '5px' }}>
                {mapping.source_count}
              </div>
            </div>
          )}
          {mapping?.target_count !== undefined && (
            <div>
              <strong style={{ color: '#666', fontSize: '12px' }}>Targets</strong>
              <div style={{ fontSize: '14px', marginTop: '5px' }}>
                {mapping.target_count}
              </div>
            </div>
          )}
          {mapping?.transformation_count !== undefined && (
            <div>
              <strong style={{ color: '#666', fontSize: '12px' }}>Transformations</strong>
              <div style={{ fontSize: '14px', marginTop: '5px' }}>
                {mapping.transformation_count}
              </div>
            </div>
          )}
        </div>
      </div>

      {structure && (
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#555' }}>Structure</h3>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '15px', 
            borderRadius: '6px',
            fontSize: '13px'
          }}>
            <div style={{ marginBottom: '10px' }}>
              <strong>Nodes:</strong> {structure.nodes?.length || 0}
            </div>
            <div>
              <strong>Edges:</strong> {structure.edges?.length || 0}
            </div>
            <div style={{ marginTop: '15px', fontSize: '12px', color: '#666' }}>
              <em>Use the Graph Explorer page for visual representation</em>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

