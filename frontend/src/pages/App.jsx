
import React, { useState } from 'react'
import UploadPage from './UploadPage.jsx'
import ViewSpecPage from './ViewSpecPage.jsx'
import LineagePage from './LineagePage.jsx'
import GraphExplorerPage from './GraphExplorerPage.jsx'
import FileBrowserPage from './FileBrowserPage.jsx'
import HierarchyPage from './HierarchyPage.jsx'

export default function App() {
  const [currentPage, setCurrentPage] = useState('browser'); // 'browser', 'upload', 'spec', 'lineage', 'graph'

  const navStyle = {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
    borderBottom: '2px solid #ddd',
    paddingBottom: '10px'
  };

  const navButtonStyle = (isActive) => ({
    padding: '10px 20px',
    background: isActive ? '#4A90E2' : '#f5f5f5',
    color: isActive ? 'white' : '#333',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: isActive ? 'bold' : 'normal',
    transition: 'all 0.2s'
  });

  return (
    <div style={{ minHeight: '100vh', background: '#fafafa' }}>
      <div style={{ padding: '20px', background: 'white', borderBottom: '2px solid #ddd' }}>
        <h1 style={{ margin: '0 0 10px 0', color: '#333' }}>Informatica Modernization Accelerator</h1>
        <div style={navStyle}>
          <button 
            style={navButtonStyle(currentPage === 'browser')}
            onClick={() => setCurrentPage('browser')}
          >
            📁 File Browser
          </button>
          <button 
            style={navButtonStyle(currentPage === 'graph')}
            onClick={() => setCurrentPage('graph')}
          >
            Graph Explorer
          </button>
          <button 
            style={navButtonStyle(currentPage === 'upload')}
            onClick={() => setCurrentPage('upload')}
          >
            Upload & Parse
          </button>
          <button 
            style={navButtonStyle(currentPage === 'spec')}
            onClick={() => setCurrentPage('spec')}
          >
            View Spec
          </button>
          <button 
            style={navButtonStyle(currentPage === 'lineage')}
            onClick={() => setCurrentPage('lineage')}
          >
            Lineage
          </button>
          <button 
            style={navButtonStyle(currentPage === 'hierarchy')}
            onClick={() => setCurrentPage('hierarchy')}
          >
            Hierarchy
          </button>
        </div>
      </div>

      <div>
        {currentPage === 'browser' && <FileBrowserPage />}
        {currentPage === 'graph' && <GraphExplorerPage />}
        {currentPage === 'upload' && <UploadPage />}
        {currentPage === 'spec' && <ViewSpecPage />}
        {currentPage === 'lineage' && <LineagePage />}
        {currentPage === 'hierarchy' && <HierarchyPage />}
      </div>
    </div>
  )
}
