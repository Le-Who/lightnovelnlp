import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../services/apiClient'
import ChapterManager from '../components/ChapterManager.jsx'
import GlossaryEditor from '../components/GlossaryEditor.jsx'
import ChapterViewer from '../components/ChapterViewer.jsx'
import RelationshipsViewer from '../components/RelationshipsViewer.jsx'
import GlossaryVersionManager from '../components/GlossaryVersionManager.jsx'
import BatchProcessor from '../components/BatchProcessor.jsx'

export default function ProjectPage() {
  const { projectId } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('chapters') // 'chapters', 'glossary', 'relationships', 'translations', 'versions', или 'batch'

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

  if (loading) return <div>Загрузка проекта...</div>
  if (!project) return <div>Проект не найден</div>

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Link 
          to="/" 
          style={{ 
            display: 'inline-block', 
            marginBottom: 16, 
            color: '#2196F3', 
            textDecoration: 'none' 
          }}
        >
          ← Назад к проектам
        </Link>
        <h2>{project.name}</h2>
        <p style={{ color: '#666' }}>Создан: {new Date(project.created_at).toLocaleDateString()}</p>
      </div>

      {/* Табы */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 24, flexWrap: 'wrap' }}>
        <button
          onClick={() => setActiveTab('chapters')}
          style={{
            padding: '12px 16px',
            border: 'none',
            backgroundColor: activeTab === 'chapters' ? '#2196F3' : '#f5f5f5',
            color: activeTab === 'chapters' ? 'white' : '#333',
            cursor: 'pointer',
            borderTopLeftRadius: 8,
            borderBottomLeftRadius: 8,
            fontSize: '0.9em'
          }}
        >
          Главы
        </button>
        <button
          onClick={() => setActiveTab('glossary')}
          style={{
            padding: '12px 16px',
            border: 'none',
            backgroundColor: activeTab === 'glossary' ? '#2196F3' : '#f5f5f5',
            color: activeTab === 'glossary' ? 'white' : '#333',
            cursor: 'pointer',
            fontSize: '0.9em'
          }}
        >
          Глоссарий
        </button>
        <button
          onClick={() => setActiveTab('relationships')}
          style={{
            padding: '12px 16px',
            border: 'none',
            backgroundColor: activeTab === 'relationships' ? '#2196F3' : '#f5f5f5',
            color: activeTab === 'relationships' ? 'white' : '#333',
            cursor: 'pointer',
            fontSize: '0.9em'
          }}
        >
          Связи
        </button>
        <button
          onClick={() => setActiveTab('translations')}
          style={{
            padding: '12px 16px',
            border: 'none',
            backgroundColor: activeTab === 'translations' ? '#2196F3' : '#f5f5f5',
            color: activeTab === 'translations' ? 'white' : '#333',
            cursor: 'pointer',
            fontSize: '0.9em'
          }}
        >
          Переводы
        </button>
        <button
          onClick={() => setActiveTab('versions')}
          style={{
            padding: '12px 16px',
            border: 'none',
            backgroundColor: activeTab === 'versions' ? '#2196F3' : '#f5f5f5',
            color: activeTab === 'versions' ? 'white' : '#333',
            cursor: 'pointer',
            fontSize: '0.9em'
          }}
        >
          Версии
        </button>
        <button
          onClick={() => setActiveTab('batch')}
          style={{
            padding: '12px 16px',
            border: 'none',
            backgroundColor: activeTab === 'batch' ? '#2196F3' : '#f5f5f5',
            color: activeTab === 'batch' ? 'white' : '#333',
            cursor: 'pointer',
            borderTopRightRadius: 8,
            borderBottomRightRadius: 8,
            fontSize: '0.9em'
          }}
        >
          Пакетная обработка
        </button>
      </div>

      {/* Контент табов */}
      {activeTab === 'chapters' && (
        <ChapterManager projectId={projectId} />
      )}
      {activeTab === 'glossary' && (
        <GlossaryEditor projectId={projectId} />
      )}
      {activeTab === 'relationships' && (
        <RelationshipsViewer projectId={projectId} />
      )}
      {activeTab === 'translations' && (
        <ChapterViewer projectId={projectId} />
      )}
      {activeTab === 'versions' && (
        <GlossaryVersionManager projectId={projectId} />
      )}
      {activeTab === 'batch' && (
        <BatchProcessor projectId={projectId} />
      )}
    </div>
  )
}
