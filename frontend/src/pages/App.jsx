
import React, { useState } from 'react'
import ViewSpecPage from './ViewSpecPage.jsx'
import LineagePage from './LineagePage.jsx'
import GraphExplorerPage from './GraphExplorerPage.jsx'
import FileBrowserPage from './FileBrowserPage.jsx'
import HierarchyPage from './HierarchyPage.jsx'
import CanonicalModelPage from './CanonicalModelPage.jsx'
import ComponentsPage from './ComponentsPage.jsx'
import SourceRepoViewPage from './SourceRepoViewPage.jsx'
import CodeViewPage from './CodeViewPage.jsx'
import CodeRepositoryPage from './CodeRepositoryPage.jsx'
import AssessmentPage from './AssessmentPage.jsx'

export default function App() {
  const [currentPage, setCurrentPage] = useState('source-repo'); // 'source-repo', 'components', 'canonical', 'code-view', 'code-repository'

  const navStyle = {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
    borderBottom: '2px solid #ddd',
    paddingBottom: '10px',
    flexWrap: 'wrap'
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
            style={navButtonStyle(currentPage === 'source-repo')}
            onClick={() => setCurrentPage('source-repo')}
          >
            📂 Source Repo View
          </button>
          <button 
            style={navButtonStyle(currentPage === 'components')}
            onClick={() => setCurrentPage('components')}
          >
            📦 Component View
          </button>
          <button 
            style={navButtonStyle(currentPage === 'canonical')}
            onClick={() => setCurrentPage('canonical')}
          >
            📊 Canonical Model
          </button>
          <button 
            style={navButtonStyle(currentPage === 'assessment')}
            onClick={() => setCurrentPage('assessment')}
          >
            📈 Assessment
          </button>
          <button 
            style={navButtonStyle(currentPage === 'code-view')}
            onClick={() => setCurrentPage('code-view')}
          >
            💻 Code View
          </button>
          <button 
            style={navButtonStyle(currentPage === 'code-repository')}
            onClick={() => setCurrentPage('code-repository')}
          >
            📁 Code Repository
          </button>
        </div>
      </div>

      <div>
        {currentPage === 'source-repo' && <SourceRepoViewPage />}
        {currentPage === 'components' && <ComponentsPage />}
        {currentPage === 'canonical' && <CanonicalModelPage />}
        {currentPage === 'assessment' && <AssessmentPage />}
        {currentPage === 'code-view' && <CodeViewPage />}
        {currentPage === 'code-repository' && <CodeRepositoryPage />}
      </div>
    </div>
  )
}
