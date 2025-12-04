import React, { useState, useEffect } from 'react';
import ModelTreeView from '../components/canonical/ModelTreeView.jsx';
import ModelOverview from '../components/canonical/ModelOverview.jsx';
import ModelBreadcrumbs from '../components/canonical/ModelBreadcrumbs.jsx';
import ModelTabs from '../components/canonical/ModelTabs.jsx';
import QuickFilters from '../components/canonical/QuickFilters.jsx';
import EnhancedSearch from '../components/canonical/EnhancedSearch.jsx';
import ModelGridView from '../components/canonical/ModelGridView.jsx';
import ModelListView from '../components/canonical/ModelListView.jsx';
import apiClient from '../services/api.js';

/**
 * Canonical Model Explorer Page
 * 
 * Provides comprehensive navigation and visualization of canonical model:
 * - Overview dashboard with statistics and charts
 * - Multiple view modes: Tree, Grid, List
 * - Enhanced navigation: Breadcrumbs, tabs, filters, search
 * - Uses generic canonical model terminology (Pipeline, Task, Transformation)
 */
export default function CanonicalModelPage() {
  const [selectedItem, setSelectedItem] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Tab management
  const [activeTab, setActiveTab] = useState('Overview');
  
  // View mode management
  const [viewMode, setViewMode] = useState('tree'); // 'tree', 'grid', 'list'
  
  // Filter management
  const [activeFilters, setActiveFilters] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  
  // Breadcrumb management
  const [breadcrumbItems, setBreadcrumbItems] = useState([]);
  
  // Component list for grid/list views
  const [allComponents, setAllComponents] = useState([]);
  const [componentsLoading, setComponentsLoading] = useState(false);

  // Load all components when switching to Components tab
  useEffect(() => {
    if (activeTab === 'Components' && allComponents.length === 0) {
      loadAllComponents();
    }
  }, [activeTab]);

  const loadAllComponents = async () => {
    setComponentsLoading(true);
    try {
      const filters = {};
      if (activeFilters.complexity && activeFilters.complexity !== 'all') {
        filters.complexity = activeFilters.complexity;
      }
      if (activeFilters.type && activeFilters.type !== 'all') {
        filters.type = activeFilters.type;
      }
      if (activeFilters.status === 'with_code') {
        filters.has_code = true;
      } else if (activeFilters.status === 'without_code') {
        filters.has_code = false;
      }
      
      const result = await apiClient.getAllComponents(filters);
      if (result.success) {
        // Combine all component types
        const combined = [
          ...(result.pipelines || []).map(p => ({ ...p, source_component_type: 'pipeline' })),
          ...(result.tasks || []).map(t => ({ ...t, source_component_type: 'task' })),
          ...(result.transformations || []).map(t => ({ ...t, source_component_type: 'transformation' })),
          ...(result.reusable_transformations || []).map(rt => ({ ...rt, source_component_type: 'reusable_transformation' })),
          ...(result.sub_pipelines || []).map(sp => ({ ...sp, source_component_type: 'sub_pipeline' }))
        ];
        
        // Apply search filter
        let filtered = combined;
        if (searchTerm) {
          const searchLower = searchTerm.toLowerCase();
          filtered = combined.filter(item => {
            const name = (item.name || item.transformation_name || '').toLowerCase();
            const type = (item.type || item.source_component_type || '').toLowerCase();
            return name.includes(searchLower) || type.includes(searchLower);
          });
        }
        
        setAllComponents(filtered);
      }
    } catch (err) {
      console.error('Error loading components:', err);
    } finally {
      setComponentsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'Components') {
      loadAllComponents();
    }
  }, [activeFilters, searchTerm]);

  const handleSelectWorkflow = async (workflow) => {
    setSelectedItem({ type: 'pipeline', name: workflow.name, data: workflow });
    setDetailData(null);
    setError(null);
    setBreadcrumbItems([{ type: 'pipeline', name: workflow.name, label: workflow.name }]);
    setActiveTab('Details');
    
    // Load workflow details
    setLoading(true);
    try {
      const result = await apiClient.getPipelineStructure(workflow.name);
      if (result.success) {
        setDetailData(result.pipeline);
      } else {
        setError(result.message || 'Failed to load pipeline details');
      }
    } catch (err) {
      setError(err.message || 'Failed to load pipeline details');
      console.error('Error loading pipeline:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSession = async (session, workflowName) => {
    setSelectedItem({ 
      type: 'task', 
      name: session.name, 
      workflowName,
      data: session 
    });
    setDetailData(session);
    setError(null);
    setBreadcrumbItems([
      { type: 'pipeline', name: workflowName, label: workflowName },
      { type: 'task', name: session.name, label: session.name }
    ]);
    setActiveTab('Details');
  };

  const handleSelectMapping = async (mapping, sessionName, workflowName) => {
    setSelectedItem({ 
      type: 'transformation', 
      name: mapping.name,
      mappingName: mapping.mapping_name,
      sessionName,
      workflowName,
      data: mapping 
    });
    setDetailData(null);
    setError(null);
    setBreadcrumbItems([
      { type: 'pipeline', name: workflowName, label: workflowName },
      { type: 'task', name: sessionName, label: sessionName },
      { type: 'transformation', name: mapping.name, label: mapping.mapping_name || mapping.name }
    ]);
    setActiveTab('Details');
    
    // Load transformation structure/details
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
      console.error('Error loading transformation structure:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBreadcrumbNavigate = (item) => {
    if (!item) {
      // Navigate to root
      setSelectedItem(null);
      setDetailData(null);
      setBreadcrumbItems([]);
      setActiveTab('Overview');
      return;
    }
    
    // Navigate to the clicked breadcrumb item
    if (item.type === 'pipeline') {
      // Find and select the pipeline
      apiClient.listPipelines().then(result => {
        if (result.success) {
          const pipeline = result.pipelines.find(p => p.name === item.name);
          if (pipeline) {
            handleSelectWorkflow(pipeline);
          }
        }
      });
    } else if (item.type === 'task') {
      // Would need to load task details
      setBreadcrumbItems([breadcrumbItems[0], item]);
      setActiveTab('Details');
    } else if (item.type === 'transformation') {
      // Would need to load transformation details
      setBreadcrumbItems([breadcrumbItems[0], breadcrumbItems[1], item]);
      setActiveTab('Details');
    }
  };

  const handleFilterChange = (newFilters) => {
    setActiveFilters(newFilters);
  };

  const handleSearch = (term) => {
    setSearchTerm(term);
  };

  const handleItemClick = (item) => {
    if (item.source_component_type === 'pipeline') {
      handleSelectWorkflow(item);
    } else if (item.source_component_type === 'task') {
      handleSelectSession(item, item.workflowName);
    } else if (item.source_component_type === 'transformation') {
      handleSelectMapping(item, item.sessionName, item.workflowName);
    }
  };

  const renderComponentsView = () => {
    if (componentsLoading) {
      return (
        <div style={{ padding: '40px', textAlign: 'center' }}>
          <div style={{ fontSize: '24px', marginBottom: '10px' }}>⏳</div>
          <div>Loading components...</div>
        </div>
      );
    }

    if (viewMode === 'tree') {
      return (
        <div style={{ display: 'flex', gap: '20px', flex: 1, overflow: 'hidden', minHeight: 0 }}>
          <div style={{ width: '350px', border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', background: 'white', display: 'flex', flexDirection: 'column' }}>
            <ModelTreeView
              onSelectMapping={handleSelectMapping}
              onSelectSession={handleSelectSession}
              onSelectWorkflow={handleSelectWorkflow}
              selectedItem={selectedItem}
            />
          </div>
          <div style={{ flex: 1, border: '1px solid #ddd', borderRadius: '8px', overflow: 'auto', background: 'white', padding: '20px' }}>
            {!selectedItem ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#666', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
                <h2 style={{ margin: '10px 0', color: '#333' }}>Select an Item to View Details</h2>
                <p style={{ margin: '5px 0', color: '#666' }}>
                  Choose a pipeline, task, or transformation from the tree view to see detailed information
                </p>
              </div>
            ) : (
              <DetailView item={selectedItem} data={detailData || selectedItem.data} />
            )}
          </div>
        </div>
      );
    } else if (viewMode === 'grid') {
      return (
        <ModelGridView
          items={allComponents}
          onItemClick={handleItemClick}
          selectedItem={selectedItem}
          groupBy="none"
          sortBy="name"
          sortOrder="asc"
        />
      );
    } else if (viewMode === 'list') {
      return (
        <ModelListView
          items={allComponents}
          onItemClick={handleItemClick}
          selectedItem={selectedItem}
          sortBy="name"
          sortOrder="asc"
        />
      );
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
      {/* Tabs */}
      <ModelTabs 
        activeTab={activeTab} 
        onTabChange={setActiveTab}
        tabs={['Overview', 'Components', 'Lineage', 'Details']}
      />

      {/* Breadcrumbs */}
      {breadcrumbItems.length > 0 && (
        <div style={{ marginBottom: '15px' }}>
          <ModelBreadcrumbs 
            items={breadcrumbItems} 
            onNavigate={handleBreadcrumbNavigate}
          />
        </div>
      )}

      {/* View Mode Toggle and Filters (for Components tab) */}
      {activeTab === 'Components' && (
        <div style={{ marginBottom: '15px' }}>
          <div style={{ display: 'flex', gap: '15px', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
              <span style={{ fontSize: '14px', color: '#666', marginRight: '10px' }}>View Mode:</span>
              {['tree', 'grid', 'list'].map(mode => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  style={{
                    padding: '6px 12px',
                    background: viewMode === mode ? '#4A90E2' : 'white',
                    color: viewMode === mode ? 'white' : '#666',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    textTransform: 'capitalize',
                    fontWeight: viewMode === mode ? '600' : '400'
                  }}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
          <EnhancedSearch
            onSearch={handleSearch}
            placeholder="Search pipelines, tasks, transformations..."
          />
          <QuickFilters
            activeFilters={activeFilters}
            onFilterChange={handleFilterChange}
          />
        </div>
      )}

      {/* Main Content */}
      <div style={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
        {activeTab === 'Overview' && (
          <ModelOverview onRefresh={loadAllComponents} />
        )}
        
        {activeTab === 'Components' && renderComponentsView()}
        
        {activeTab === 'Lineage' && (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔗</div>
            <h2 style={{ margin: '10px 0', color: '#333' }}>Lineage Visualization</h2>
            <p style={{ margin: '5px 0', color: '#666' }}>
              Lineage visualization coming soon
            </p>
          </div>
        )}
        
        {activeTab === 'Details' && (
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
                  Choose a pipeline, task, or transformation to see detailed information
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
        )}
      </div>
    </div>
  );
}

/**
 * Detail View Component
 * Shows detailed information based on selected item type
 * Uses generic canonical model terminology
 */
function DetailView({ item, data }) {
  if (item.type === 'pipeline') {
    return <PipelineDetailView pipeline={data} />;
  } else if (item.type === 'task') {
    return <TaskDetailView task={data} workflowName={item.workflowName} />;
  } else if (item.type === 'transformation') {
    return <TransformationDetailView transformation={data} sessionName={item.sessionName} workflowName={item.workflowName} />;
  }
  
  return <div>Unknown item type: {item.type}</div>;
}

/**
 * Pipeline Detail View (formerly Workflow)
 */
function PipelineDetailView({ pipeline }) {
  // Support both generic terminology (tasks) and Informatica terminology (sessions)
  const tasks = pipeline?.tasks || pipeline?.sessions || [];
  
  return (
    <div>
      <div style={{ marginBottom: '30px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#333' }}>
          {pipeline?.name || 'Unknown Pipeline'}
        </h2>
        <div style={{ fontSize: '14px', color: '#666' }}>
          Pipeline Details
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
              {pipeline?.type || 'N/A'}
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
 * Task Detail View (formerly Session)
 */
function TaskDetailView({ task, workflowName }) {
  const transformations = task?.transformations || task?.mappings || [];
  
  return (
    <div>
      <div style={{ marginBottom: '30px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#333' }}>
          {task?.name || 'Unknown Task'}
        </h2>
        <div style={{ fontSize: '14px', color: '#666' }}>
          Task in pipeline: <strong>{workflowName}</strong>
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
              {task?.type || 'N/A'}
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

      {task?.properties && Object.keys(task.properties).length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#555' }}>Properties</h3>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '15px', 
            borderRadius: '6px',
            fontSize: '13px'
          }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(task.properties, null, 2)}
            </pre>
          </div>
        </div>
      )}

      <div>
        <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Transformations</h3>
        {transformations.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            No transformations found
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {transformations.map((transformation, idx) => (
              <div
                key={transformation.name || idx}
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
                  {transformation.transformation_name || transformation.mapping_name || transformation.name}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  {transformation.complexity && (
                    <span style={{ 
                      marginRight: '10px',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      background: transformation.complexity === 'LOW' ? '#4CAF50' : 
                                 transformation.complexity === 'MEDIUM' ? '#FF9800' : '#F44336',
                      color: 'white'
                    }}>
                      {transformation.complexity}
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
 * Transformation Detail View (formerly Mapping)
 */
function TransformationDetailView({ transformation, sessionName, workflowName }) {
  const structure = transformation?.structure;
  const complexity = transformation?.complexity || transformation?.data?.complexity;
  const transformations = structure?.nodes?.filter(n => n.type === 'transformation') || [];
  const sources = structure?.nodes?.filter(n => n.type === 'source') || [];
  const targets = structure?.nodes?.filter(n => n.type === 'target') || [];
  
  return (
    <div>
      <div style={{ marginBottom: '30px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#333' }}>
          {transformation?.transformation_name || transformation?.mapping_name || transformation?.name || 'Unknown Transformation'}
        </h2>
        <div style={{ fontSize: '14px', color: '#666' }}>
          <div>Pipeline: <strong>{workflowName}</strong> → Task: <strong>{sessionName}</strong></div>
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
