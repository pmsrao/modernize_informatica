
import React from 'react'
import UploadPage from './UploadPage.jsx'
import ViewSpecPage from './ViewSpecPage.jsx'
import LineagePage from './LineagePage.jsx'

export default function App() {
  return (
    <div style={{ padding: 20 }}>
      <h1>Informatica Modernization UI</h1>
      <UploadPage />
      <ViewSpecPage />
      <LineagePage />
    </div>
  )
}
