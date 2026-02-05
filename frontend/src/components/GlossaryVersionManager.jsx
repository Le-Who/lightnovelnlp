import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'

export default function GlossaryVersionManager({ projectId }) {
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(false)
  const [creatingVersion, setCreatingVersion] = useState(false)
  const [newVersionName, setNewVersionName] = useState('')
  const [newVersionDescription, setNewVersionDescription] = useState('')

  const loadVersions = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/glossary/${projectId}/versions`)
      setVersions(res.data)
    } catch (e) {
      console.error('Error loading versions:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      loadVersions()
    }
  }, [projectId])

  const createVersion = async () => {
    if (!newVersionName.trim()) {
      alert('Введите название версии')
      return
    }

    setCreatingVersion(true)
    try {
      await api.post(`/glossary/${projectId}/versions`, {
        name: newVersionName,
        description: newVersionDescription
      })
      
      setNewVersionName('')
      setNewVersionDescription('')
      loadVersions()
      alert('Версия создана успешно!')
    } catch (e) {
      console.error('Error creating version:', e)
      alert('Ошибка при создании версии')
    } finally {
      setCreatingVersion(false)
    }
  }

  const restoreVersion = async (versionId) => {
    if (!confirm('Вы уверены, что хотите восстановить эту версию? Текущий глоссарий будет заменен.')) {
      return
    }

    try {
      await api.post(`/glossary/versions/${versionId}/restore`)
      alert('Глоссарий восстановлен успешно!')
      window.location.reload()
    } catch (e) {
      console.error('Error restoring version:', e)
      alert('Ошибка при восстановлении версии')
    }
  }

  if (loading) return <div>Загрузка версий...</div>

  return (
    <div>
      <h3>Версии глоссария</h3>
      
      {/* Создание новой версии */}
      <div style={{ 
        border: '1px solid #ddd', 
        padding: 16, 
        borderRadius: 8, 
        marginBottom: 24,
        backgroundColor: '#f9f9f9'
      }}>
        <h4 style={{ margin: '0 0 16px 0' }}>Создать новую версию</h4>
        
        <div style={{ display: 'grid', gap: 12 }}>
          <div>
            <label style={{ display: 'block', marginBottom: 4 }}>Название версии:</label>
            <input
              type="text"
              value={newVersionName}
              onChange={(e) => setNewVersionName(e.target.value)}
              placeholder="Например: Версия 1.0"
              style={{ width: '100%', padding: 8, border: '1px solid #ddd', borderRadius: 4 }}
            />
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: 4 }}>Описание:</label>
            <textarea
              value={newVersionDescription}
              onChange={(e) => setNewVersionDescription(e.target.value)}
              placeholder="Описание изменений в этой версии"
              style={{ 
                width: '100%', 
                padding: 8, 
                border: '1px solid #ddd', 
                borderRadius: 4,
                minHeight: 60,
                resize: 'vertical'
              }}
            />
          </div>
          
          <button
            onClick={createVersion}
            disabled={creatingVersion}
            style={{
              padding: '8px 16px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: creatingVersion ? 'not-allowed' : 'pointer',
              opacity: creatingVersion ? 0.7 : 1
            }}
          >
            {creatingVersion ? 'Создание...' : 'Создать версию'}
          </button>
        </div>
      </div>

      {/* Список версий */}
      {versions.length === 0 ? (
        <p>Версии отсутствуют. Создайте первую версию глоссария.</p>
      ) : (
        <div style={{ display: 'grid', gap: 16 }}>
          {versions.map((version) => (
            <div 
              key={version.version_id} 
              style={{ 
                border: '1px solid #ddd', 
                padding: 16, 
                borderRadius: 8,
                backgroundColor: 'white'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <h4 style={{ margin: '0 0 4px 0' }}>
                    {version.name || `Версия ${version.version_number}`}
                  </h4>
                  <div style={{ fontSize: '0.9em', color: '#666', marginBottom: 8 }}>
                    Создана: {new Date(version.created_at).toLocaleString()}
                  </div>
                  {version.description && (
                    <div style={{ fontSize: '0.9em', color: '#666', marginBottom: 8 }}>
                      {version.description}
                    </div>
                  )}
                </div>
                
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.8em', color: '#666', marginBottom: 4 }}>
                    Терминов: {version.terms_count}
                  </div>
                  <div style={{ fontSize: '0.8em', color: '#666', marginBottom: 8 }}>
                    Утверждено: {version.approved_terms_count}
                  </div>
                  
                  <button
                    onClick={() => restoreVersion(version.version_id)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#FF9800',
                      color: 'white',
                      border: 'none',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: '0.9em'
                    }}
                  >
                    Восстановить
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
