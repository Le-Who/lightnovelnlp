import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '@/services/apiClient'
import { NeonProjectPage } from '@/components/themes/neon/NeonProjectPage'

export default function ProjectPage() {
  const { projectId } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadProject = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/projects/${projectId}`)
      setProject(res.data)
    } catch (e) {
      console.error('Error loading project:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      loadProject()
    }
  }, [projectId])

  return (
    <NeonProjectPage
      project={project}
      loading={loading}
      projectId={projectId}
      onRefresh={loadProject}
    />
  )
}
