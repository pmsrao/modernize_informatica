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
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [selectedFileInfo, setSelectedFileInfo] = useState(null);
  const [inputMode, setInputMode] = useState('select'); // 'select' or 'manual'

  useEffect(() => {
    loadUploadedFiles();
    // Try to get last uploaded file ID
    const lastFileId = localStorage.getItem('lastUploadedFileId');
    if (lastFileId) {
      setMappingId(lastFileId);
      setInputMode('manual');
    }
  }, []);

  useEffect(() => {
    if (mappingId && inputMode === 'select') {
      loadFileInfo(mappingId);
    }
  }, [mappingId, inputMode]);

  const loadUploadedFiles = async () => {
    setLoadingFiles(true);
    try {
      const result = await apiClient.listAllFiles('mapping');
      if (result.success) {
        setUploadedFiles(result.files || []);
      }
    } catch (err) {
      console.error('Error loading files:', err);
    } finally {
      setLoadingFiles(false);
    }
  };

  const loadFileInfo = async (fileId) => {
    try {
      const fileInfo = await apiClient.getFileInfo(fileId);
      setSelectedFileInfo(fileInfo);
      if (fileInfo.file_type !== 'mapping') {
        setError(`⚠️ This file is a "${fileInfo.file_type}", but View Spec requires a "mapping" file.`);
      } else {
        setError(null);
      }
    } catch (err) {
      console.error('Error loading file info:', err);
    }
  };

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

  const getFileTypeColor = (type) => {
    return type === 'mapping' ? '#4A90E2' : '#FF6B6B';
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #ddd', paddingBottom: '15px' }}>
        <h2 style={{ margin: 0, color: '#333' }}>View Mapping Specification</h2>
        <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
          View mapping specifications and generated code. <strong>Requires a mapping XML file.</strong>
        </p>
      </div>

      {/* File Selection */}
      <div style={{ 
        marginBottom: '20px', 
        padding: '20px', 
        background: '#f5f5f5', 
        borderRadius: '8px',
        border: '1px solid #ddd'
      }}>
        <div style={{ marginBottom: '15px', display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={() => setInputMode('select')}
            style={{
              padding: '8px 16px',
              backgroundColor: inputMode === 'select' ? '#4A90E2' : '#f5f5f5',
              color: inputMode === 'select' ? 'white' : '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: inputMode === 'select' ? 'bold' : 'normal'
            }}
          >
            📁 Select from Uploaded Mappings
          </button>
          <button
            onClick={() => setInputMode('manual')}
            style={{
              padding: '8px 16px',
              backgroundColor: inputMode === 'manual' ? '#4A90E2' : '#f5f5f5',
              color: inputMode === 'manual' ? 'white' : '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: inputMode === 'manual' ? 'bold' : 'normal'
            }}
          >
            ✏️ Enter Mapping ID Manually
          </button>
        </div>

        {inputMode === 'select' && (
          <div>
            <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
              Select Mapping File:
            </label>
            {loadingFiles ? (
              <div style={{ padding: '10px', textAlign: 'center' }}>Loading mapping files...</div>
            ) : uploadedFiles.length === 0 ? (
              <div style={{ padding: '15px', background: '#fff3cd', borderRadius: '4px', color: '#856404' }}>
                No mapping files found. Upload mapping files in the File Browser or Upload & Parse tab.
              </div>
            ) : (
              <select
                value={mappingId || ''}
                onChange={(e) => {
                  setMappingId(e.target.value);
                  setSpec(null);
                  setPysparkCode(null);
                  setDltCode(null);
                  setSqlCode(null);
                  setError(null);
                }}
                style={{
                  padding: '10px',
                  width: '100%',
                  maxWidth: '600px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                <option value="">-- Select a mapping file --</option>
                {uploadedFiles.map((f) => (
                  <option key={f.file_id} value={f.file_id}>
                    📋 {f.filename} - {new Date(f.uploaded_at).toLocaleDateString()}
                  </option>
                ))}
              </select>
            )}
            {selectedFileInfo && (
              <div style={{ 
                marginTop: '15px', 
                padding: '10px', 
                background: selectedFileInfo.file_type === 'mapping' ? '#d4edda' : '#f8d7da',
                borderRadius: '4px',
                border: `2px solid ${getFileTypeColor(selectedFileInfo.file_type)}`
              }}>
                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                  Selected: {selectedFileInfo.filename}
                </div>
                <div style={{ fontSize: '12px' }}>
                  Type: <span style={{
                    padding: '2px 8px',
                    background: getFileTypeColor(selectedFileInfo.file_type),
                    color: 'white',
                    borderRadius: '3px',
                    fontWeight: 'bold'
                  }}>{selectedFileInfo.file_type}</span>
                  {selectedFileInfo.file_type !== 'mapping' && (
                    <span style={{ color: '#c62828', marginLeft: '10px' }}>
                      ⚠️ This is not a mapping file!
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {inputMode === 'manual' && (
          <div>
            <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
              Mapping ID or File ID:
            </label>
            <input
              type="text"
              placeholder="Enter mapping ID or file ID"
              value={mappingId}
              onChange={(e) => {
                setMappingId(e.target.value);
                setSpec(null);
                setPysparkCode(null);
                setDltCode(null);
                setSqlCode(null);
                setError(null);
                setSelectedFileInfo(null);
              }}
              style={{
                padding: '10px',
                width: '100%',
                maxWidth: '600px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </div>
        )}

        <div style={{ marginTop: '15px' }}>
          <button
            onClick={handleLoad}
            disabled={loading || !mappingId || (selectedFileInfo && selectedFileInfo.file_type !== 'mapping')}
            style={{
              padding: '10px 20px',
              backgroundColor: (loading || !mappingId || (selectedFileInfo && selectedFileInfo.file_type !== 'mapping')) ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: (loading || !mappingId || (selectedFileInfo && selectedFileInfo.file_type !== 'mapping')) ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '14px'
            }}
          >
            {loading ? 'Loading...' : '📄 Load Specification'}
          </button>
        </div>
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
