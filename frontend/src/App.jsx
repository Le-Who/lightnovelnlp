import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage.jsx'
import ProjectPage from './pages/ProjectPage.jsx'

export default function App() {
  return (
    <Router>
      <div style={{ maxWidth: 960, margin: '0 auto', padding: 24 }}>
        <h1>Ranobe Translator</h1>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/projects/:projectId" element={<ProjectPage />} />
        </Routes>
      </div>
    </Router>
  )
}
