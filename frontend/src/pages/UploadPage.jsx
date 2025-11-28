import React, { useState, useEffect } from 'react';
import apiClient from '../services/api';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const [enhanceModel, setEnhanceModel] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState(null);
  const [uploadMode, setUploadMode] = useState('upload'); // 'upload' or 'select'

  useEffect(() => {
    loadUploadedFiles();
  }, []);

  useEffect(() => {
    if (selectedFileId) {
      loadFileInfo(selectedFileId);
    }
  }, [selectedFileId]);

  const loadUploadedFiles = async () => {
    setLoadingFiles(true);
    try {
      const result = await apiClient.listAllFiles();
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
      setUploadResult({
        file_id: fileInfo.file_id,
        filename: fileInfo.filename,
        file_size: fileInfo.file_size,
        file_type: fileInfo.file_type,
        uploaded_at: fileInfo.uploaded_at
      });
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load file info');
      console.error('Error loading file info:', err);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Validate file type
      if (!selectedFile.name.endsWith('.xml')) {
        setError('Please upload an XML file');
        return;
      }
      setFile(selectedFile);
      setError(null);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const result = await apiClient.uploadFile(file);
      setUploadResult(result);
      
      // Store file ID in localStorage for later use
      if (result.file_id) {
        localStorage.setItem('lastUploadedFileId', result.file_id);
      }
    } catch (err) {
      setError(err.message || 'Upload failed');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleParseMapping = async () => {
    if (!uploadResult?.file_id) {
      setError('Please upload a file first');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Call parseMapping with enhance_model option
      const result = await apiClient.request('/api/v1/parse/mapping', {
        method: 'POST',
        body: JSON.stringify({
          file_id: uploadResult.file_id,
          enhance_model: enhanceModel
        })
      });
      setUploadResult({ ...uploadResult, parsed: result });
    } catch (err) {
      setError(err.message || 'Parsing failed');
      console.error('Parse error:', err);
    } finally {
      setUploading(false);
    }
  };

  const getFileTypeColor = (type) => {
    const colors = {
      'mapping': '#4A90E2',
      'workflow': '#50C878',
      'session': '#FFA500',
      'worklet': '#9B59B6',
      'unknown': '#95A5A6'
    };
    return colors[type] || colors.unknown;
  };

  const getFileTypeIcon = (type) => {
    const icons = {
      'mapping': '📋',
      'workflow': '🔄',
      'session': '⚙️',
      'worklet': '📦',
      'unknown': '❓'
    };
    return icons[type] || icons.unknown;
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h2>Upload & Parse Informatica XML</h2>
      
      {/* Mode Selection */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', borderBottom: '2px solid #ddd', paddingBottom: '15px' }}>
        <button
          onClick={() => {
            setUploadMode('upload');
            setSelectedFileId(null);
            setUploadResult(null);
            setFile(null);
          }}
          style={{
            padding: '10px 20px',
            backgroundColor: uploadMode === 'upload' ? '#007bff' : '#f5f5f5',
            color: uploadMode === 'upload' ? 'white' : '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: uploadMode === 'upload' ? 'bold' : 'normal'
          }}
        >
          📤 Upload New File
        </button>
        <button
          onClick={() => {
            setUploadMode('select');
            setFile(null);
            loadUploadedFiles();
          }}
          style={{
            padding: '10px 20px',
            backgroundColor: uploadMode === 'select' ? '#007bff' : '#f5f5f5',
            color: uploadMode === 'select' ? 'white' : '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: uploadMode === 'select' ? 'bold' : 'normal'
          }}
        >
          📁 Select from Uploaded Files
        </button>
      </div>

      {/* Upload Mode */}
      {uploadMode === 'upload' && (
        <div style={{ marginBottom: '20px' }}>
          <input
            type="file"
            accept=".xml"
            onChange={handleFileChange}
            disabled={uploading}
            style={{ marginBottom: '10px', padding: '8px', width: '100%', maxWidth: '400px' }}
          />
          <br />
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            style={{
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: uploading ? 'not-allowed' : 'pointer',
              opacity: (!file || uploading) ? 0.6 : 1
            }}
          >
            {uploading ? 'Uploading...' : 'Upload File'}
          </button>
        </div>
      )}

      {/* Select Mode */}
      {uploadMode === 'select' && (
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
            Select Uploaded File:
          </label>
          {loadingFiles ? (
            <div style={{ padding: '20px', textAlign: 'center' }}>Loading files...</div>
          ) : uploadedFiles.length === 0 ? (
            <div style={{ padding: '20px', background: '#fff3cd', borderRadius: '4px', color: '#856404' }}>
              No files uploaded yet. Switch to "Upload New File" mode to upload files.
            </div>
          ) : (
            <select
              value={selectedFileId || ''}
              onChange={(e) => setSelectedFileId(e.target.value)}
              style={{
                padding: '10px',
                width: '100%',
                maxWidth: '500px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              <option value="">-- Select a file --</option>
              {uploadedFiles.map((f) => (
                <option key={f.file_id} value={f.file_id}>
                  {getFileTypeIcon(f.file_type)} {f.filename} ({f.file_type}) - {new Date(f.uploaded_at).toLocaleDateString()}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

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

      {uploadResult && (
        <div style={{
          padding: '15px',
          backgroundColor: '#d4edda',
          borderRadius: '4px',
          marginBottom: '10px',
          border: '2px solid #28a745'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <span style={{ fontSize: '24px' }}>{getFileTypeIcon(uploadResult.file_type)}</span>
            <h3 style={{ margin: 0 }}>
              {uploadMode === 'select' ? 'File Selected' : 'Upload Successful'}
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '15px' }}>
            <div>
              <strong>File ID:</strong> 
              <div style={{ 
                fontFamily: 'monospace', 
                fontSize: '12px', 
                background: '#f8f9fa', 
                padding: '4px 8px', 
                borderRadius: '4px',
                marginTop: '4px',
                wordBreak: 'break-all'
              }}>
                {uploadResult.file_id}
              </div>
            </div>
            <div>
              <strong>Filename:</strong> 
              <div style={{ marginTop: '4px' }}>{uploadResult.filename}</div>
            </div>
            <div>
              <strong>File Size:</strong> {(uploadResult.file_size / 1024).toFixed(2)} KB
            </div>
            <div>
              <strong>File Type:</strong>
              <span style={{
                marginLeft: '8px',
                padding: '4px 10px',
                background: getFileTypeColor(uploadResult.file_type),
                color: 'white',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {uploadResult.file_type}
              </span>
            </div>
          </div>
          
          {uploadResult.file_type === 'mapping' && (
            <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #28a745' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <input
                  type="checkbox"
                  checked={enhanceModel}
                  onChange={(e) => setEnhanceModel(e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <span style={{ fontSize: '14px', fontWeight: '500' }}>
                  Enhance Model (AI enhancement + save to Neo4j)
                </span>
              </label>
              <button
                onClick={handleParseMapping}
                disabled={uploading}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: uploading ? 'not-allowed' : 'pointer',
                  opacity: uploading ? 0.6 : 1,
                  fontWeight: 'bold'
                }}
              >
                {uploading ? 'Parsing...' : 'Parse Mapping'}
              </button>
            </div>
          )}

          {uploadResult.file_type === 'workflow' && (
            <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #28a745' }}>
              <p style={{ marginBottom: '10px', fontSize: '14px', color: '#666' }}>
                Workflow files can be parsed and visualized in the <strong>Lineage</strong> tab.
              </p>
              <button
                onClick={() => {
                  localStorage.setItem('lastUploadedFileId', uploadResult.file_id);
                  alert('File ID saved! Go to the Lineage tab to view the DAG.');
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#50C878',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                Use in Lineage Viewer
              </button>
            </div>
          )}

          {uploadResult.parsed && (
            <div style={{ marginTop: '15px' }}>
              <h4>Parsed Result:</h4>
              <pre style={{
                backgroundColor: '#f8f9fa',
                padding: '10px',
                borderRadius: '4px',
                overflow: 'auto',
                maxHeight: '400px'
              }}>
                {JSON.stringify(uploadResult.parsed, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
