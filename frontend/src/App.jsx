import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage.jsx'
import ProjectPage from './pages/ProjectPage.jsx'
// import TestPage from './pages/TestPage.jsx'
import { AppLayout } from './components/layout/AppLayout'
import { ThemeSwitcher } from './components/ThemeSwitcher'

export default function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/projects/:projectId" element={<ProjectPage />} />
          {/* <Route path="/test" element={<TestPage />} /> */}
        </Routes>
        <div className="fixed bottom-4 right-4 z-50">
          <ThemeSwitcher />
        </div>
      </AppLayout>
    </Router>
  )
}
