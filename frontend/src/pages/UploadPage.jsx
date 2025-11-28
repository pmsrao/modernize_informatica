import React, { useState } from 'react';
import apiClient from '../services/api';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const [enhanceModel, setEnhanceModel] = useState(true);

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

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Upload Informatica XML</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <input
          type="file"
          accept=".xml"
          onChange={handleFileChange}
          disabled={uploading}
          style={{ marginBottom: '10px' }}
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
            cursor: uploading ? 'not-allowed' : 'pointer'
          }}
        >
          {uploading ? 'Uploading...' : 'Upload File'}
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

      {uploadResult && (
        <div style={{
          padding: '15px',
          backgroundColor: '#d4edda',
          borderRadius: '4px',
          marginBottom: '10px'
        }}>
          <h3>Upload Successful</h3>
          <p><strong>File ID:</strong> {uploadResult.file_id}</p>
          <p><strong>Filename:</strong> {uploadResult.filename}</p>
          <p><strong>File Size:</strong> {(uploadResult.file_size / 1024).toFixed(2)} KB</p>
          <p><strong>File Type:</strong> {uploadResult.file_type}</p>
          
          {uploadResult.file_type === 'mapping' && (
            <div style={{ marginTop: '15px' }}>
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
                  opacity: uploading ? 0.6 : 1
                }}
              >
                {uploading ? 'Parsing...' : 'Parse Mapping'}
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
