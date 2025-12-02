import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';

/**
 * Assessment Page
 * 
 * Displays pre-migration assessment summary including:
 * - Repository statistics
 * - Complexity metrics
 * - Migration blockers
 * - Effort estimates
 * - Migration wave recommendations
 */
export default function AssessmentPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [waves, setWaves] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    loadAssessmentData();
  }, []);

  const loadAssessmentData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [summaryData, analysisData, wavesData] = await Promise.all([
        apiClient.getAssessmentReport('summary'),
        apiClient.getAssessmentAnalysis(),
        apiClient.getMigrationWaves(10)
      ]);
      
      setSummary(summaryData);
      setAnalysis(analysisData);
      setWaves(wavesData);
    } catch (err) {
      console.error('Error loading assessment data:', err);
      setError(err.message || 'Failed to load assessment data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
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
          <div>Loading assessment data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        padding: '20px', 
        background: '#ffebee',
        border: '1px solid #f44336',
        borderRadius: '4px',
        color: '#c62828',
        margin: '20px'
      }}>
        <strong>Error:</strong> {error}
        <button 
          onClick={loadAssessmentData}
          style={{
            marginTop: '10px',
            padding: '8px 16px',
            background: '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

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
        <h1 style={{ margin: 0, color: '#333' }}>Pre-Migration Assessment</h1>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          Repository analysis, migration blockers, effort estimates, and wave planning
        </p>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '10px',
        marginBottom: '20px',
        borderBottom: '1px solid #ddd'
      }}>
        {['summary', 'blockers', 'waves', 'analysis'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 20px',
              background: activeTab === tab ? '#4A90E2' : 'transparent',
              color: activeTab === tab ? 'white' : '#333',
              border: 'none',
              borderBottom: activeTab === tab ? '3px solid #4A90E2' : '3px solid transparent',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: activeTab === tab ? 'bold' : 'normal',
              textTransform: 'capitalize'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ 
        flex: 1, 
        overflow: 'auto',
        background: 'white',
        borderRadius: '8px',
        padding: '20px'
      }}>
        {activeTab === 'summary' && <SummaryView summary={summary} />}
        {activeTab === 'blockers' && <BlockersView blockers={analysis?.blockers || []} />}
        {activeTab === 'waves' && <WavesView waves={waves} />}
        {activeTab === 'analysis' && <AnalysisView analysis={analysis} />}
      </div>
    </div>
  );
}

/**
 * Summary View Component
 */
function SummaryView({ summary }) {
  if (!summary) return <div>No summary data available</div>;

  const stats = summary.repository_statistics || {};
  const complexity = summary.overall_complexity || 'UNKNOWN';
  const effort = summary.total_effort_days || 0;
  const blockers = summary.blocker_count || 0;
  const waveCount = summary.wave_count || 0;

  const complexityColor = {
    'LOW': '#4CAF50',
    'MEDIUM': '#FF9800',
    'HIGH': '#F44336'
  }[complexity] || '#666';

  return (
    <div>
      <h2 style={{ marginTop: 0, color: '#333' }}>Assessment Summary</h2>
      
      {/* Key Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <MetricCard
          label="Total Workflows"
          value={stats.total_workflows || 0}
          icon="🔄"
        />
        <MetricCard
          label="Total Mappings"
          value={stats.total_mappings || 0}
          icon="📋"
        />
        <MetricCard
          label="Total Transformations"
          value={stats.total_transformations || 0}
          icon="⚙️"
        />
        <MetricCard
          label="Overall Complexity"
          value={complexity}
          icon="📊"
          color={complexityColor}
        />
        <MetricCard
          label="Total Effort (Days)"
          value={effort.toFixed(1)}
          icon="⏱️"
        />
        <MetricCard
          label="Migration Blockers"
          value={blockers}
          icon="⚠️"
          color={blockers > 0 ? '#F44336' : '#4CAF50'}
        />
        <MetricCard
          label="Migration Waves"
          value={waveCount}
          icon="🌊"
        />
      </div>

      {/* Key Findings */}
      {summary.key_findings && summary.key_findings.length > 0 && (
        <div style={{
          background: '#f5f5f5',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '20px'
        }}>
          <h3 style={{ marginTop: 0, color: '#333' }}>Key Findings</h3>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            {summary.key_findings.map((finding, idx) => (
              <li key={idx} style={{ marginBottom: '10px', color: '#666' }}>
                {finding}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Component Distribution */}
      {stats.component_type_distribution && (
        <div>
          <h3 style={{ color: '#333' }}>Component Distribution</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '15px'
          }}>
            {Object.entries(stats.component_type_distribution).map(([key, value]) => (
              <div key={key} style={{
                padding: '15px',
                background: '#f9f9f9',
                borderRadius: '6px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#4A90E2' }}>
                  {value}
                </div>
                <div style={{ fontSize: '12px', color: '#666', textTransform: 'capitalize' }}>
                  {key.replace(/_/g, ' ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Blockers View Component
 */
function BlockersView({ blockers }) {
  if (!blockers || blockers.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>✅</div>
        <h2>No Migration Blockers Found</h2>
        <p>All components appear to be ready for migration.</p>
      </div>
    );
  }

  const severityColors = {
    'HIGH': '#F44336',
    'MEDIUM': '#FF9800',
    'LOW': '#FFC107'
  };

  return (
    <div>
      <h2 style={{ marginTop: 0, color: '#333' }}>Migration Blockers</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Found {blockers.length} potential migration blocker{blockers.length !== 1 ? 's' : ''}
      </p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {blockers.map((blocker, idx) => (
          <div
            key={idx}
            style={{
              padding: '20px',
              borderLeft: `4px solid ${severityColors[blocker.severity] || '#666'}`,
              background: '#f9f9f9',
              borderRadius: '4px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
              <div>
                <h3 style={{ margin: 0, color: '#333' }}>{blocker.component_name}</h3>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                  {blocker.component_type} • {blocker.blocker_type}
                </div>
              </div>
              <span style={{
                padding: '4px 12px',
                background: severityColors[blocker.severity] || '#666',
                color: 'white',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {blocker.severity}
              </span>
            </div>
            <p style={{ margin: '10px 0', color: '#666' }}>{blocker.description}</p>
            <div style={{
              padding: '10px',
              background: '#e3f2fd',
              borderRadius: '4px',
              marginTop: '10px'
            }}>
              <strong>Recommendation:</strong> {blocker.recommendation}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Waves View Component
 */
function WavesView({ waves }) {
  if (!waves || !waves.waves || waves.waves.length === 0) {
    return <div>No migration waves available</div>;
  }

  return (
    <div>
      <h2 style={{ marginTop: 0, color: '#333' }}>Migration Wave Plan</h2>
      
      {waves.wave_summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '20px',
          marginBottom: '30px'
        }}>
          <MetricCard label="Total Waves" value={waves.wave_summary.total_waves} icon="🌊" />
          <MetricCard label="Avg Wave Size" value={waves.wave_summary.average_wave_size?.toFixed(1)} icon="📦" />
          <MetricCard label="Total Effort (Days)" value={waves.wave_summary.total_effort_days?.toFixed(1)} icon="⏱️" />
          <MetricCard label="Avg Effort/Wave" value={waves.wave_summary.average_effort_per_wave?.toFixed(1)} icon="📊" />
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {waves.waves.map((wave, idx) => (
          <div
            key={idx}
            style={{
              padding: '20px',
              border: '1px solid #ddd',
              borderRadius: '8px',
              background: '#f9f9f9'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h3 style={{ margin: 0, color: '#333' }}>Wave {wave.wave_number}</h3>
              <div style={{ display: 'flex', gap: '15px', fontSize: '14px', color: '#666' }}>
                <span>📦 {wave.components?.length || 0} components</span>
                <span>⏱️ {wave.total_effort_days?.toFixed(1)} days</span>
                {wave.dependencies_satisfied && (
                  <span style={{ color: '#4CAF50' }}>✅ Dependencies OK</span>
                )}
              </div>
            </div>
            
            {wave.complexity_distribution && (
              <div style={{ marginBottom: '15px' }}>
                <strong>Complexity:</strong>{' '}
                LOW: {wave.complexity_distribution.LOW || 0}, {' '}
                MEDIUM: {wave.complexity_distribution.MEDIUM || 0}, {' '}
                HIGH: {wave.complexity_distribution.HIGH || 0}
              </div>
            )}

            {wave.components && wave.components.length > 0 && (
              <div>
                <strong>Components:</strong>
                <ul style={{ marginTop: '10px', paddingLeft: '20px' }}>
                  {wave.components.slice(0, 10).map((comp, compIdx) => (
                    <li key={compIdx} style={{ marginBottom: '5px', color: '#666' }}>
                      {comp.name} ({comp.type}) - {comp.complexity || 'N/A'}
                    </li>
                  ))}
                  {wave.components.length > 10 && (
                    <li style={{ color: '#999', fontStyle: 'italic' }}>
                      ... and {wave.components.length - 10} more
                    </li>
                  )}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Analysis View Component
 */
function AnalysisView({ analysis }) {
  if (!analysis) return <div>No analysis data available</div>;

  return (
    <div>
      <h2 style={{ marginTop: 0, color: '#333' }}>Detailed Analysis</h2>
      
      {/* Effort Estimates */}
      {analysis.effort_estimates && (
        <div style={{ marginBottom: '30px' }}>
          <h3 style={{ color: '#333' }}>Effort Estimates</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '15px'
          }}>
            {analysis.effort_estimates.effort_by_complexity && Object.entries(analysis.effort_estimates.effort_by_complexity).map(([complexity, days]) => (
              <div key={complexity} style={{
                padding: '15px',
                background: '#f9f9f9',
                borderRadius: '6px'
              }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#4A90E2' }}>
                  {days.toFixed(1)} days
                </div>
                <div style={{ fontSize: '12px', color: '#666', textTransform: 'uppercase' }}>
                  {complexity} Complexity
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Patterns */}
      {analysis.patterns && analysis.patterns.common_transformation_patterns && (
        <div style={{ marginBottom: '30px' }}>
          <h3 style={{ color: '#333' }}>Common Transformation Patterns</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '10px'
          }}>
            {analysis.patterns.common_transformation_patterns.slice(0, 10).map((pattern, idx) => (
              <div key={idx} style={{
                padding: '10px',
                background: '#f9f9f9',
                borderRadius: '4px'
              }}>
                <strong>{pattern.transformation_type}</strong>: {pattern.usage_count} uses
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dependencies */}
      {analysis.dependencies && (
        <div>
          <h3 style={{ color: '#333' }}>Dependencies</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '15px'
          }}>
            <div style={{ padding: '15px', background: '#f9f9f9', borderRadius: '6px' }}>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#4A90E2' }}>
                {analysis.dependencies.total_dependencies || 0}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Dependencies</div>
            </div>
            <div style={{ padding: '15px', background: '#f9f9f9', borderRadius: '6px' }}>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#4CAF50' }}>
                {analysis.dependencies.independent_mappings?.length || 0}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Independent Mappings</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Metric Card Component
 */
function MetricCard({ label, value, icon, color = '#4A90E2' }) {
  return (
    <div style={{
      padding: '20px',
      background: '#f9f9f9',
      borderRadius: '8px',
      textAlign: 'center',
      border: `2px solid ${color}20`
    }}>
      <div style={{ fontSize: '32px', marginBottom: '10px' }}>{icon}</div>
      <div style={{ fontSize: '28px', fontWeight: 'bold', color, marginBottom: '5px' }}>
        {value}
      </div>
      <div style={{ fontSize: '12px', color: '#666', textTransform: 'uppercase' }}>
        {label}
      </div>
    </div>
  );
}

