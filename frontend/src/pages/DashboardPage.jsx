import React, { useEffect, useState } from 'react'
import api from '../services/apiClient'
import ProjectList from '../components/ProjectList.jsx'

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
      <div style={{ marginBottom: 30 }}>
        <h2>Добро пожаловать в Light Novel Translator!</h2>
        <p>Создайте новый проект для начала работы с переводами.</p>
        
        <div style={{ marginTop: 20, padding: 20, backgroundColor: '#f8f9fa', borderRadius: 8 }}>
          <h3>🔧 Доступ к функциям API:</h3>
          <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap', marginTop: 15 }}>
            <a 
              href="/api-tools.html" 
              target="_blank" 
              rel="noopener noreferrer"
              style={{
                padding: '10px 20px',
                backgroundColor: '#3498db',
                color: 'white',
                textDecoration: 'none',
                borderRadius: 5,
                display: 'inline-block'
              }}
            >
              📝 API Tools (Формы)
            </a>
            <a 
              href="/docs" 
              target="_blank" 
              rel="noopener noreferrer"
              style={{
                padding: '10px 20px',
                backgroundColor: '#27ae60',
                color: 'white',
                textDecoration: 'none',
                borderRadius: 5,
                display: 'inline-block'
              }}
            >
              📚 Swagger Documentation
            </a>
            <a 
              href="/Light_Novel_NLP_API.postman_collection.json" 
              download
              style={{
                padding: '10px 20px',
                backgroundColor: '#e74c3c',
                color: 'white',
                textDecoration: 'none',
                borderRadius: 5,
                display: 'inline-block'
              }}
            >
              📦 Postman Collection
            </a>
          </div>
          <p style={{ marginTop: 15, fontSize: '14px', color: '#666' }}>
            💡 <strong>Совет:</strong> Используйте API Tools для быстрого тестирования функций или Swagger для полной документации API.
          </p>
        </div>
      </div>

      <form onSubmit={createProject} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Название проекта" />
        <button type="submit">Создать</button>
      </form>
      {loading ? <div>Загрузка…</div> : <ProjectList projects={projects} />}
    </div>
  )
}
