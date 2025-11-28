import React, { useState, useEffect } from 'react';
import apiClient from '../services/api.js';

export default function FileBrowserPage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [selectedFile, setSelectedFile] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.listAllFiles(filterType === 'all' ? null : filterType);
      if (result.success) {
        setFiles(result.files || []);
        setSummary(result.by_type || {});
      }
    } catch (err) {
      setError(err.message || 'Failed to load files');
      console.error('Error loading files:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, [filterType]);

  const handleDirectoryUpload = async (event) => {
    const selectedFiles = Array.from(event.target.files);
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setError(null);
    setUploadProgress({ uploaded: 0, total: selectedFiles.length });

    try {
      const formData = new FormData();
      selectedFiles.forEach(file => {
        if (file.name.endsWith('.xml')) {
          formData.append('files', file);
        }
      });

      const result = await apiClient.uploadDirectory(formData);
      
      if (result.success) {
        setUploadProgress({
          uploaded: result.summary.uploaded,
          total: result.summary.total_files,
          errors: result.summary.errors
        });
        
        // Reload files
        await loadFiles();
        
        // Show success message
        setTimeout(() => {
          setUploadProgress(null);
        }, 3000);
      }
    } catch (err) {
      setError(err.message || 'Directory upload failed');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleFileClick = (file) => {
    setSelectedFile(file);
    // Store in localStorage for other pages
    localStorage.setItem('lastUploadedFileId', file.file_id);
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

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const filteredFiles = filterType === 'all' 
    ? files 
    : files.filter(f => f.file_type === filterType);

  return (
    <div style={{ padding: '20px', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #ddd', paddingBottom: '20px' }}>
        <h1 style={{ margin: 0, color: '#333' }}>File Browser</h1>
        <p style={{ margin: '5px 0', color: '#666' }}>
          Upload and manage Informatica XML files
        </p>
      </div>

      {/* Upload Section */}
      <div style={{ 
        marginBottom: '20px', 
        padding: '20px', 
        background: '#f5f5f5', 
        borderRadius: '8px',
        border: '2px dashed #ddd'
      }}>
        <h3 style={{ marginTop: 0 }}>Upload Directory</h3>
        <p style={{ color: '#666', fontSize: '14px', marginBottom: '15px' }}>
          Select multiple XML files to upload at once. All files will be scanned and categorized automatically.
        </p>
        <input
          type="file"
          multiple
          accept=".xml"
          onChange={handleDirectoryUpload}
          disabled={uploading}
          style={{ display: 'none' }}
          id="directory-upload"
        />
        <label
          htmlFor="directory-upload"
          style={{
            display: 'inline-block',
            padding: '10px 20px',
            background: uploading ? '#ccc' : '#4A90E2',
            color: 'white',
            borderRadius: '6px',
            cursor: uploading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold'
          }}
        >
          {uploading ? 'Uploading...' : '📁 Select Multiple Files'}
        </label>
        
        {uploadProgress && (
          <div style={{ marginTop: '15px', padding: '10px', background: '#d4edda', borderRadius: '6px' }}>
            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
              Upload Progress: {uploadProgress.uploaded}/{uploadProgress.total} files
            </div>
            {uploadProgress.errors && uploadProgress.errors.length > 0 && (
              <div style={{ marginTop: '10px', fontSize: '12px', color: '#721c24' }}>
                <strong>Errors:</strong>
                <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                  {uploadProgress.errors.map((err, idx) => (
                    <li key={idx}>{err.filename}: {err.error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Summary Statistics */}
      {summary && Object.keys(summary).length > 0 && (
        <div style={{ 
          display: 'flex', 
          gap: '15px', 
          marginBottom: '20px',
          padding: '15px',
          background: 'white',
          borderRadius: '8px',
          border: '1px solid #ddd'
        }}>
          <div style={{ fontWeight: 'bold', marginRight: '10px' }}>Summary:</div>
          {Object.entries(summary).map(([type, fileList]) => (
            <div key={type} style={{ 
              padding: '5px 15px', 
              background: getFileTypeColor(type),
              color: 'white',
              borderRadius: '4px',
              fontSize: '14px'
            }}>
              {getFileTypeIcon(type)} {type}: {fileList.length}
            </div>
          ))}
        </div>
      )}

      {/* Filter and Search */}
      <div style={{ 
        display: 'flex', 
        gap: '15px', 
        marginBottom: '15px',
        alignItems: 'center'
      }}>
        <label style={{ fontWeight: 'bold' }}>Filter by Type:</label>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          style={{
            padding: '8px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px',
            cursor: 'pointer'
          }}
        >
          <option value="all">All Types ({files.length})</option>
          <option value="mapping">Mappings ({summary?.mapping?.length || 0})</option>
          <option value="workflow">Workflows ({summary?.workflow?.length || 0})</option>
          <option value="session">Sessions ({summary?.session?.length || 0})</option>
          <option value="worklet">Worklets ({summary?.worklet?.length || 0})</option>
        </select>
      </div>

      {error && (
        <div style={{
          padding: '15px',
          background: '#ffebee',
          color: '#c62828',
          borderRadius: '6px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {/* File List */}
      <div style={{ flex: 1, overflow: 'auto', border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center' }}>Loading files...</div>
        ) : filteredFiles.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            <p>No files found. Upload files using the directory upload above.</p>
          </div>
        ) : (
          <div style={{ padding: '15px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #ddd', background: '#f5f5f5' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Type</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Filename</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Size</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Uploaded</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredFiles.map((file) => (
                  <tr
                    key={file.file_id}
                    onClick={() => handleFileClick(file)}
                    style={{
                      borderBottom: '1px solid #eee',
                      cursor: 'pointer',
                      background: selectedFile?.file_id === file.file_id ? '#E3F2FD' : 'white',
                      transition: 'background 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      if (selectedFile?.file_id !== file.file_id) {
                        e.currentTarget.style.background = '#f5f5f5';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedFile?.file_id !== file.file_id) {
                        e.currentTarget.style.background = 'white';
                      }
                    }}
                  >
                    <td style={{ padding: '12px' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '4px 10px',
                        background: getFileTypeColor(file.file_type),
                        color: 'white',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 'bold'
                      }}>
                        {getFileTypeIcon(file.file_type)} {file.file_type}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontWeight: '500' }}>{file.filename}</td>
                    <td style={{ padding: '12px', color: '#666' }}>{formatFileSize(file.file_size)}</td>
                    <td style={{ padding: '12px', color: '#666', fontSize: '12px' }}>
                      {new Date(file.uploaded_at).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleFileClick(file);
                        }}
                        style={{
                          padding: '5px 12px',
                          background: '#4A90E2',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Selected File Details Panel */}
      {selectedFile && (
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'white',
          borderTop: '2px solid #4A90E2',
          padding: '20px',
          boxShadow: '0 -2px 10px rgba(0,0,0,0.1)',
          maxHeight: '40vh',
          overflow: 'auto',
          zIndex: 1000
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 style={{ margin: 0 }}>File Details: {selectedFile.filename}</h3>
            <button
              onClick={() => setSelectedFile(null)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ×
            </button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px' }}>
            <div>
              <strong>File ID:</strong> {selectedFile.file_id}
            </div>
            <div>
              <strong>Type:</strong> 
              <span style={{
                marginLeft: '10px',
                padding: '4px 10px',
                background: getFileTypeColor(selectedFile.file_type),
                color: 'white',
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                {selectedFile.file_type}
              </span>
            </div>
            <div>
              <strong>Size:</strong> {formatFileSize(selectedFile.file_size)}
            </div>
            <div>
              <strong>Uploaded:</strong> {new Date(selectedFile.uploaded_at).toLocaleString()}
            </div>
          </div>
          <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
            <button
              onClick={() => {
                // Navigate to appropriate page based on file type
                if (selectedFile.file_type === 'mapping') {
                  window.location.hash = '#upload';
                } else if (selectedFile.file_type === 'workflow') {
                  window.location.hash = '#lineage';
                }
                setSelectedFile(null);
              }}
              style={{
                padding: '8px 16px',
                background: '#4A90E2',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              {selectedFile.file_type === 'mapping' ? 'Parse Mapping' : 
               selectedFile.file_type === 'workflow' ? 'View DAG' : 
               'View Details'}
            </button>
            <button
              onClick={() => {
                navigator.clipboard.writeText(selectedFile.file_id);
                alert('File ID copied to clipboard!');
              }}
              style={{
                padding: '8px 16px',
                background: '#666',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Copy File ID
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

