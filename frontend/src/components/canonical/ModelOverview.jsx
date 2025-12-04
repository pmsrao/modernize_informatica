import React, { useState, useEffect } from 'react';
import apiClient from '../../services/api.js';
import ComponentDistributionChart from './ComponentDistributionChart.jsx';
import ComplexityChart from './ComplexityChart.jsx';

/**
 * Overview Dashboard Component for Canonical Model
 * 
 * Displays statistics cards, charts, and health indicators
 * using generic canonical model terminology.
 */
export default function ModelOverview({ onRefresh }) {
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
      const result = await apiClient.getCanonicalOverview();
      if (result.success) {
        setOverview(result.overview);
      } else {
        setError(result.message || 'Failed to load overview');
      }
    } catch (err) {
      setError(err.message || 'Failed to load overview');
      console.error('Error loading overview:', err);
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
  const complexity = overview.complexity_distribution || {};
  const typeDistribution = overview.transformation_type_distribution || {};
  const health = overview.component_health || {};

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
        <h2 style={{ margin: 0, color: '#333' }}>Canonical Model Overview</h2>
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
          color="#4A90E2"
        />
        <StatCard 
          title="Tasks" 
          value={counts.tasks || 0}
          icon="⚙️"
          color="#4CAF50"
        />
        <StatCard 
          title="Transformations" 
          value={counts.transformations || 0}
          icon="🔄"
          color="#FF9800"
        />
        <StatCard 
          title="Reusable Transformations" 
          value={counts.reusable_transformations || 0}
          icon="🔁"
          color="#9C27B0"
        />
      </div>

      {/* Charts Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <div style={{
          background: 'white',
          border: '1px solid #ddd',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Complexity Distribution</h3>
          <ComplexityChart data={complexity} />
        </div>
        
        <div style={{
          background: 'white',
          border: '1px solid #ddd',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Transformation Type Distribution</h3>
          <ComponentDistributionChart data={typeDistribution} />
        </div>
      </div>

      {/* Component Health */}
      <div style={{
        background: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '20px'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '15px'
        }}>
          <h3 style={{ margin: 0, color: '#555' }}>Component Health</h3>
          <div style={{ 
            fontSize: '12px', 
            color: '#666',
            fontStyle: 'italic'
          }}>
            Based on {health.total || 0} transformation(s)
          </div>
        </div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '15px',
          marginBottom: '15px'
        }}>
          <HealthIndicator 
            label="With Code" 
            value={health.with_code || 0}
            total={health.total || 0}
            color="#4CAF50"
            tooltip="Transformations that have generated code files"
          />
          <HealthIndicator 
            label="Without Code" 
            value={health.without_code || 0}
            total={health.total || 0}
            color="#FF9800"
            tooltip="Transformations that don't have generated code yet"
          />
          <HealthIndicator 
            label="Validated" 
            value={health.validated || 0}
            total={health.total || 0}
            color="#2196F3"
            tooltip="Transformations with code that have been validated (quality_score > 0)"
          />
          <HealthIndicator 
            label="AI Reviewed" 
            value={health.ai_reviewed || 0}
            total={health.total || 0}
            color="#9C27B0"
            tooltip="Transformations with code that have been reviewed by AI agents"
          />
          <HealthIndicator 
            label="AI Fixed" 
            value={health.ai_fixed || 0}
            total={health.total || 0}
            color="#00BCD4"
            tooltip="Transformations with code that have been fixed by AI agents"
          />
          <HealthIndicator 
            label="Needs Review" 
            value={health.needs_review || 0}
            total={health.total || 0}
            color="#F44336"
            tooltip="Transformations that need review (without code or not yet validated)"
          />
        </div>
        <div style={{
          padding: '12px',
          background: '#f5f5f5',
          borderRadius: '6px',
          fontSize: '12px',
          color: '#666',
          lineHeight: '1.6'
        }}>
          <strong>Understanding Component Health:</strong>
          <ul style={{ margin: '8px 0 0 20px', padding: 0 }}>
            <li><strong>With Code:</strong> Transformations that have generated code files (PySpark, SQL, etc.)</li>
            <li><strong>Without Code:</strong> Transformations that haven't been converted to code yet</li>
            <li><strong>Validated:</strong> Transformations with code that have passed validation checks (quality_score > 0)</li>
            <li><strong>AI Reviewed:</strong> Transformations with code that have been reviewed by AI agents (CodeReviewAgent)</li>
            <li><strong>AI Fixed:</strong> Transformations with code that have been fixed by AI agents (CodeFixAgent)</li>
            <li><strong>Needs Review:</strong> Transformations requiring attention (no code or not validated)</li>
          </ul>
          <div style={{ marginTop: '8px', fontSize: '11px', fontStyle: 'italic' }}>
            <strong>Process Flow:</strong> Canonical Model → Code Generation → Validation (quality_score) → AI Review → AI Fix (if needed)
          </div>
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
function HealthIndicator({ label, value, total, color, tooltip }) {
  const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
  
  return (
    <div title={tooltip || label}>
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

