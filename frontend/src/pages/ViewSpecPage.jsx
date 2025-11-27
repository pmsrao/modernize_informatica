import React, { useState, useEffect } from 'react';
import apiClient from '../services/api';

export default function ViewSpecPage() {
  const [mappingId, setMappingId] = useState('');
  const [loading, setLoading] = useState(false);
  const [spec, setSpec] = useState(null);
  const [pysparkCode, setPysparkCode] = useState(null);
  const [dltCode, setDltCode] = useState(null);
  const [sqlCode, setSqlCode] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('spec');

  useEffect(() => {
    // Try to get last uploaded file ID
    const lastFileId = localStorage.getItem('lastUploadedFileId');
    if (lastFileId) {
      setMappingId(lastFileId);
    }
  }, []);

  const handleLoad = async () => {
    if (!mappingId) {
      setError('Please enter a mapping ID');
      return;
    }

    setLoading(true);
    setError(null);
    setSpec(null);
    setPysparkCode(null);
    setDltCode(null);
    setSqlCode(null);

    try {
      // Generate spec
      const specResult = await apiClient.generateSpec(mappingId);
      if (specResult.success) {
        setSpec(specResult.code);
      }

      // Generate PySpark code
      try {
        const pysparkResult = await apiClient.generatePySpark(mappingId);
        if (pysparkResult.success) {
          setPysparkCode(pysparkResult.code);
        }
      } catch (err) {
        console.warn('PySpark generation failed:', err);
      }

      // Generate DLT code
      try {
        const dltResult = await apiClient.generateDLT(mappingId);
        if (dltResult.success) {
          setDltCode(dltResult.code);
        }
      } catch (err) {
        console.warn('DLT generation failed:', err);
      }

      // Generate SQL code
      try {
        const sqlResult = await apiClient.generateSQL(mappingId);
        if (sqlResult.success) {
          setSqlCode(sqlResult.code);
        }
      } catch (err) {
        console.warn('SQL generation failed:', err);
      }
    } catch (err) {
      setError(err.message || 'Failed to load mapping');
      console.error('Load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const downloadCode = (code, filename) => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>View Mapping Specification</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Enter mapping ID or file ID"
          value={mappingId}
          onChange={(e) => setMappingId(e.target.value)}
          style={{
            padding: '8px',
            width: '300px',
            marginRight: '10px',
            borderRadius: '4px',
            border: '1px solid #ccc'
          }}
        />
        <button
          onClick={handleLoad}
          disabled={loading}
          style={{
            padding: '8px 16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Loading...' : 'Load'}
        </button>
      </div>

      {error && (
        <div style={{
          padding: '10px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          borderRadius: '4px',
          marginBottom: '10px'
        }}>
          Error: {error}
        </div>
      )}

      {(spec || pysparkCode || dltCode || sqlCode) && (
        <div>
          <div style={{ borderBottom: '1px solid #ccc', marginBottom: '20px' }}>
            <button
              onClick={() => setActiveTab('spec')}
              style={{
                padding: '10px 20px',
                border: 'none',
                backgroundColor: activeTab === 'spec' ? '#007bff' : 'transparent',
                color: activeTab === 'spec' ? 'white' : '#007bff',
                cursor: 'pointer'
              }}
            >
              Specification
            </button>
            <button
              onClick={() => setActiveTab('pyspark')}
              style={{
                padding: '10px 20px',
                border: 'none',
                backgroundColor: activeTab === 'pyspark' ? '#007bff' : 'transparent',
                color: activeTab === 'pyspark' ? 'white' : '#007bff',
                cursor: 'pointer'
              }}
            >
              PySpark
            </button>
            <button
              onClick={() => setActiveTab('dlt')}
              style={{
                padding: '10px 20px',
                border: 'none',
                backgroundColor: activeTab === 'dlt' ? '#007bff' : 'transparent',
                color: activeTab === 'dlt' ? 'white' : '#007bff',
                cursor: 'pointer'
              }}
            >
              DLT
            </button>
            <button
              onClick={() => setActiveTab('sql')}
              style={{
                padding: '10px 20px',
                border: 'none',
                backgroundColor: activeTab === 'sql' ? '#007bff' : 'transparent',
                color: activeTab === 'sql' ? 'white' : '#007bff',
                cursor: 'pointer'
              }}
            >
              SQL
            </button>
          </div>

          <div style={{ position: 'relative' }}>
            {activeTab === 'spec' && spec && (
              <div>
                <button
                  onClick={() => downloadCode(spec, 'mapping_spec.md')}
                  style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    padding: '5px 10px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Download
                </button>
                <pre style={{
                  backgroundColor: '#f8f9fa',
                  padding: '15px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '600px',
                  whiteSpace: 'pre-wrap'
                }}>
                  {spec}
                </pre>
              </div>
            )}

            {activeTab === 'pyspark' && pysparkCode && (
              <div>
                <button
                  onClick={() => downloadCode(pysparkCode, 'mapping_pyspark.py')}
                  style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    padding: '5px 10px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Download
                </button>
                <pre style={{
                  backgroundColor: '#f8f9fa',
                  padding: '15px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '600px'
                }}>
                  {pysparkCode}
                </pre>
              </div>
            )}

            {activeTab === 'dlt' && dltCode && (
              <div>
                <button
                  onClick={() => downloadCode(dltCode, 'mapping_dlt.py')}
                  style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    padding: '5px 10px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Download
                </button>
                <pre style={{
                  backgroundColor: '#f8f9fa',
                  padding: '15px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '600px'
                }}>
                  {dltCode}
                </pre>
              </div>
            )}

            {activeTab === 'sql' && sqlCode && (
              <div>
                <button
                  onClick={() => downloadCode(sqlCode, 'mapping.sql')}
                  style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    padding: '5px 10px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Download
                </button>
                <pre style={{
                  backgroundColor: '#f8f9fa',
                  padding: '15px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '600px'
                }}>
                  {sqlCode}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
