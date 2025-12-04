import React, { useState, useEffect } from 'react';
import apiClient from '../../services/api.js';

/**
 * Assessment Overview Component
 * 
 * Enhanced overview for assessment with:
 * - Key metrics
 * - Migration readiness score
 * - Risk indicators
 */
export default function AssessmentOverview({ onRefresh }) {
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
      const [summaryData, analysisData] = await Promise.all([
        apiClient.getAssessmentReport('summary'),
        apiClient.getAssessmentAnalysis()
      ]);
      
      if (summaryData && analysisData) {
        const stats = summaryData.repository_statistics || {};
        const complexity = summaryData.overall_complexity || 'UNKNOWN';
        const effort = summaryData.total_effort_days || 0;
        const blockers = summaryData.blocker_count || 0;
        const waveCount = summaryData.wave_count || 0;
        
        // Calculate readiness score (0-100)
        const totalComponents = (stats.total_workflows || 0) + (stats.total_mappings || 0);
        const blockerRatio = totalComponents > 0 ? (blockers / totalComponents) : 0;
        const readinessScore = Math.max(0, Math.min(100, Math.round((1 - blockerRatio) * 100)));
        
        setOverview({
          stats,
          complexity,
          effort,
          blockers,
          waveCount,
          readinessScore,
          analysis: analysisData
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to load overview');
      console.error('Error loading assessment overview:', err);
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

  const complexityColor = {
    'LOW': '#4CAF50',
    'MEDIUM': '#FF9800',
    'HIGH': '#F44336'
  }[overview.complexity] || '#666';

  const readinessColor = overview.readinessScore >= 80 ? '#4CAF50' : 
                        overview.readinessScore >= 60 ? '#FF9800' : '#F44336';

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
        <h2 style={{ margin: 0, color: '#333' }}>Assessment Overview</h2>
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

      {/* Key Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: '12px',
        marginBottom: '30px'
      }}>
        <StatCard
          label="Total Workflows"
          value={overview.stats.total_workflows || 0}
          icon="🔄"
          color="#4A90E2"
        />
        <StatCard
          label="Total Mappings"
          value={overview.stats.total_mappings || 0}
          icon="📋"
          color="#4A90E2"
        />
        <StatCard
          label="Overall Complexity"
          value={overview.complexity}
          icon="📊"
          color={complexityColor}
        />
        <StatCard
          label="Total Effort (Days)"
          value={overview.effort.toFixed(1)}
          icon="⏱️"
          color="#FF9800"
        />
        <StatCard
          label="Migration Blockers"
          value={overview.blockers}
          icon="⚠️"
          color={overview.blockers > 0 ? '#F44336' : '#4CAF50'}
        />
        <StatCard
          label="Migration Waves"
          value={overview.waveCount}
          icon="🌊"
          color="#9C27B0"
        />
      </div>

      {/* Readiness Score */}
      <div style={{
        background: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 15px 0', color: '#555' }}>Migration Readiness</h3>
        <div style={{ textAlign: 'center' }}>
          <div style={{ 
            fontSize: '64px', 
            fontWeight: 'bold', 
            color: readinessColor,
            marginBottom: '10px'
          }}>
            {overview.readinessScore}%
          </div>
          <div style={{ fontSize: '14px', color: '#666' }}>
            {overview.readinessScore >= 80 ? 'Ready for Migration' : 
             overview.readinessScore >= 60 ? 'Mostly Ready' : 
             'Needs Review'}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Statistics Card Component
 */
function StatCard({ label, value, icon, color }) {
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
      <div style={{ fontSize: '12px', color: '#666' }}>{label}</div>
    </div>
  );
}

