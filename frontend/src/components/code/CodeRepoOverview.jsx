import React, { useState, useEffect } from 'react';
import apiClient from '../../services/api.js';

/**
 * Code Repository Overview Component
 * 
 * Displays statistics for code repository structure:
 * - Repository structure summary
 * - File counts by type
 * - Quality metrics
 */
export default function CodeRepoOverview({ onRefresh }) {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      // Use code overview endpoint
      const result = await apiClient.getCodeOverview();
      if (result.success) {
        setOverview(result.overview);
      } else {
        setError(result.message || 'Failed to load overview');
      }
    } catch (err) {
      setError(err.message || 'Failed to load overview');
      console.error('Error loading code repo overview:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadOverview();
    if (onRefresh) onRefresh();
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '24px', marginBottom: '10px' }}>⏳</div>
        <div>Loading overview...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', background: '#ffebee', border: '1px solid #f44336', borderRadius: '4px', color: '#c62828' }}>
        <strong>Error:</strong> {error}
        <button onClick={handleRefresh} style={{ marginLeft: '10px', padding: '5px 10px' }}>
          Retry
        </button>
      </div>
    );
  }

  if (!overview) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
        No overview data available
      </div>
    );
  }

  const quality = overview.quality_distribution || {};

  return (
    <div style={{ padding: '20px' }}>
      {/* Header with Actions */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px',
        borderBottom: '2px solid #ddd',
        paddingBottom: '15px'
      }}>
        <h2 style={{ margin: 0, color: '#333' }}>Code Repository Overview</h2>
        <button 
          onClick={handleRefresh}
          style={{
            padding: '8px 16px',
            background: '#4A90E2',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          🔄 Refresh
        </button>
      </div>

      {/* Statistics Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: '12px',
        marginBottom: '30px'
      }}>
        <StatCard 
          title="Total Files" 
          value={overview.total_files || 0}
          icon="📄"
          color="#4A90E2"
        />
        <StatCard 
          title="Code Types" 
          value={Object.keys(overview.code_types || {}).length}
          icon="💻"
          color="#4CAF50"
        />
        <StatCard 
          title="Total Size" 
          value={formatBytes(overview.total_size || 0)}
          icon="💾"
          color="#FF9800"
        />
      </div>

      {/* Quality Distribution */}
      <div style={{
        background: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Quality Distribution</h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '15px'
        }}>
          <HealthIndicator 
            label="High Quality (≥80)" 
            value={quality.high || 0}
            total={overview.total_files || 0}
            color="#4CAF50"
          />
          <HealthIndicator 
            label="Medium Quality (60-79)" 
            value={quality.medium || 0}
            total={overview.total_files || 0}
            color="#FF9800"
          />
          <HealthIndicator 
            label="Low Quality (<60)" 
            value={quality.low || 0}
            total={overview.total_files || 0}
            color="#F44336"
          />
        </div>
      </div>

      {/* Code Types Distribution */}
      {overview.code_types && Object.keys(overview.code_types).length > 0 && (
        <div style={{
          background: 'white',
          border: '1px solid #ddd',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Code Types Distribution</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {Object.entries(overview.code_types)
              .sort(([_, a], [__, b]) => b - a)
              .map(([codeType, count]) => (
                <div key={codeType} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', color: '#333' }}>
                    {codeType.toUpperCase()}
                  </span>
                  <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#4A90E2' }}>{count}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Statistics Card Component
 */
function StatCard({ title, value, icon, color }) {
  return (
    <div style={{
      background: 'white',
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '12px',
      textAlign: 'center',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <div style={{ fontSize: '24px', marginBottom: '8px' }}>{icon}</div>
      <div style={{ fontSize: '28px', fontWeight: 'bold', color: color, marginBottom: '4px' }}>
        {value}
      </div>
      <div style={{ fontSize: '12px', color: '#666' }}>{title}</div>
    </div>
  );
}

/**
 * Health Indicator Component
 */
function HealthIndicator({ label, value, total, color }) {
  const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
  
  return (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        marginBottom: '5px',
        fontSize: '14px'
      }}>
        <span style={{ color: '#666' }}>{label}</span>
        <span style={{ fontWeight: 'bold', color: color }}>{value}</span>
      </div>
      <div style={{
        width: '100%',
        height: '8px',
        background: '#f0f0f0',
        borderRadius: '4px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${percentage}%`,
          height: '100%',
          background: color,
          transition: 'width 0.3s ease'
        }} />
      </div>
      <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
        {percentage}%
      </div>
    </div>
  );
}

