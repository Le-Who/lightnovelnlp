import React, { useEffect, useState } from 'react'
import api from '../services/apiClient'
import ProjectList from '../components/ProjectList.js'

export default function DashboardPage() {
  const [projects, setProjects] = useState([])
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.get('/projects/')
      setProjects(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const createProject = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    try {
      await api.post('/projects/', { name })
      setName('')
      load()
    } catch (e) {
      console.error(e)
      alert('Ошибка создания проекта')
    }
  }

  return (
    <div>
      <form onSubmit={createProject} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Название проекта" />
        <button type="submit">Создать</button>
      </form>
      {loading ? <div>Загрузка…</div> : <ProjectList projects={projects} />}
    </div>
  )
}
