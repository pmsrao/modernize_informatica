
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
  const [hoveredButton, setHoveredButton] = useState(null);

  const navButtonStyle = (isActive) => ({
    padding: '12px 20px',
    background: isActive 
      ? 'linear-gradient(135deg, #4A90E2 0%, #357ABD 100%)' 
      : 'transparent',
    color: isActive ? '#FFFFFF' : '#555',
    border: isActive ? 'none' : '1px solid #e0e0e0',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: isActive ? '600' : '500',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative',
    boxShadow: isActive 
      ? '0 4px 12px rgba(74, 144, 226, 0.25), 0 2px 4px rgba(74, 144, 226, 0.15)' 
      : 'none',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    minHeight: '44px',
    whiteSpace: 'nowrap'
  });

  return (
    <div style={{ minHeight: '100vh', background: '#fafafa' }}>
      {/* Fixed Header */}
      <div style={{ 
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        background: 'linear-gradient(to bottom, #ffffff 0%, #fafafa 100%)',
        borderBottom: '1px solid #e8e8e8',
        boxShadow: '0 2px 12px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.05)'
      }}>
        <div style={{ 
          padding: '18px 24px',
          maxWidth: '100%',
          margin: '0 auto'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '16px'
          }}>
            <h1 style={{ 
              margin: 0, 
              color: '#1a1a1a',
              fontSize: '26px',
              fontWeight: '700',
              letterSpacing: '-0.5px',
              background: 'linear-gradient(135deg, #1a1a1a 0%, #4A90E2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Informatica Modernization Accelerator
            </h1>
          </div>
          <div style={{
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap',
            borderTop: '1px solid #f0f0f0',
            paddingTop: '14px'
          }}>
            {[
              { id: 'source-repo', icon: '📂', label: 'Source Repo View' },
              { id: 'components', icon: '📦', label: 'Component View' },
              { id: 'canonical', icon: '📊', label: 'Canonical Model' },
              { id: 'assessment', icon: '📈', label: 'Assessment' },
              { id: 'code-view', icon: '💻', label: 'Code View' },
              { id: 'code-repository', icon: '📁', label: 'Code Repository' }
            ].map((item) => {
              const isActive = currentPage === item.id;
              const isHovered = hoveredButton === item.id && !isActive;
              
              return (
                <button
                  key={item.id}
                  style={{
                    ...navButtonStyle(isActive),
                    background: isActive 
                      ? 'linear-gradient(135deg, #4A90E2 0%, #357ABD 100%)' 
                      : isHovered ? '#f5f5f5' : 'transparent',
                    transform: isHovered ? 'translateY(-1px)' : 'translateY(0)',
                    boxShadow: isActive 
                      ? '0 4px 12px rgba(74, 144, 226, 0.25), 0 2px 4px rgba(74, 144, 226, 0.15)' 
                      : isHovered ? '0 2px 8px rgba(0, 0, 0, 0.08)' : 'none',
                    borderColor: isActive ? 'transparent' : isHovered ? '#d0d0d0' : '#e0e0e0'
                  }}
                  onMouseEnter={() => setHoveredButton(item.id)}
                  onMouseLeave={() => setHoveredButton(null)}
                  onClick={() => setCurrentPage(item.id)}
                >
                  <span style={{ fontSize: '18px', lineHeight: '1' }}>{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content with top margin to account for fixed header */}
      <div style={{ marginTop: '150px' }}>
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
