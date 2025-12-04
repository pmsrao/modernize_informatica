import React, { useState, useEffect } from 'react';
import apiClient from '../../services/api.js';

/**
 * Components Overview Component
 * 
 * Displays statistics for components:
 * - Component counts by type
 * - Components with/without metadata
 * - Parsing status
 */
export default function ComponentsOverview({ onRefresh }) {
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
      const result = await apiClient.getAllComponents();
      if (result.success) {
        const counts = result.counts || {};
        const components = {
          pipelines: result.pipelines || [],
          tasks: result.tasks || [],
          transformations: result.transformations || [],
          reusable_transformations: result.reusable_transformations || [],
          sub_pipelines: result.sub_pipelines || []
        };
        
        // Calculate metadata status
        let withMetadata = 0;
        let withoutMetadata = 0;
        
        Object.values(components).flat().forEach(comp => {
          if (comp.file_metadata) {
            withMetadata++;
          } else {
            withoutMetadata++;
          }
        });
        
        setOverview({
          counts,
          with_metadata: withMetadata,
          without_metadata: withoutMetadata,
          total: withMetadata + withoutMetadata
        });
      } else {
        setError(result.message || 'Failed to load overview');
      }
    } catch (err) {
      setError(err.message || 'Failed to load overview');
      console.error('Error loading components overview:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadOverview();
    if (onRefresh) onRefresh();
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

  const counts = overview.counts || {};

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
        <h2 style={{ margin: 0, color: '#333' }}>Components Overview</h2>
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
          title="Pipelines" 
          value={counts.pipelines || 0}
          icon="📊"
          color="#50C878"
        />
        <StatCard 
          title="Tasks" 
          value={counts.tasks || 0}
          icon="⚙️"
          color="#FFA500"
        />
        <StatCard 
          title="Transformations" 
          value={counts.transformations || 0}
          icon="📋"
          color="#4A90E2"
        />
        <StatCard 
          title="Reusable Transformations" 
          value={counts.reusable_transformations || 0}
          icon="🔧"
          color="#E74C3C"
        />
        <StatCard 
          title="Sub Pipelines" 
          value={counts.sub_pipelines || 0}
          icon="📦"
          color="#9B59B6"
        />
        <StatCard 
          title="Total Components" 
          value={overview.total || 0}
          icon="📦"
          color="#607D8B"
        />
      </div>

      {/* Metadata Status */}
      <div style={{
        background: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '20px'
      }}>
        <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Metadata Status</h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '15px'
        }}>
          <HealthIndicator 
            label="With Metadata" 
            value={overview.with_metadata || 0}
            total={overview.total || 0}
            color="#4CAF50"
          />
          <HealthIndicator 
            label="Without Metadata" 
            value={overview.without_metadata || 0}
            total={overview.total || 0}
            color="#FF9800"
          />
        </div>
      </div>
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

