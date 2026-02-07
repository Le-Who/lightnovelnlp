import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage.jsx'
import ProjectPage from './pages/ProjectPage.jsx'
import { AppLayout } from './components/layout/AppLayout'

export default function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/projects/:projectId" element={<ProjectPage />} />
        </Routes>
      </AppLayout>
    </Router>
  )
}
