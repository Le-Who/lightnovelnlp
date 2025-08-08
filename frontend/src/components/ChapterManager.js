import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'

export default function ChapterManager({ projectId }) {
  const [chapters, setChapters] = useState([])
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState({})
  const [newChapter, setNewChapter] = useState({ title: '', original_text: '' })

  const loadChapters = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/projects/${projectId}/chapters`)
      setChapters(res.data)
    } catch (e) {
      console.error('Error loading chapters:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      loadChapters()
    }
  }, [projectId])

  const createChapter = async (e) => {
    e.preventDefault()
    if (!newChapter.title.trim() || !newChapter.original_text.trim()) return

    try {
      await api.post(`/projects/${projectId}/chapters`, {
        ...newChapter,
        project_id: projectId
      })
      setNewChapter({ title: '', original_text: '' })
      loadChapters()
    } catch (e) {
      console.error('Error creating chapter:', e)
      alert('Ошибка создания главы')
    }
  }

  const analyzeChapter = async (chapterId) => {
    setAnalyzing(prev => ({ ...prev, [chapterId]: true }))
    
    try {
      const res = await api.post(`/processing/chapters/${chapterId}/analyze`)
      const taskId = res.data.task_id
      
      // Опрашиваем статус задачи
      const checkStatus = async () => {
        try {
          const statusRes = await api.get(`/processing/tasks/${taskId}/status`)
          const status = statusRes.data.status
          
          if (status === 'SUCCESS') {
            alert(`Анализ завершен! Извлечено терминов: ${statusRes.data.result.saved_terms}`)
            setAnalyzing(prev => ({ ...prev, [chapterId]: false }))
          } else if (status === 'FAILURE') {
            alert('Ошибка анализа главы')
            setAnalyzing(prev => ({ ...prev, [chapterId]: false }))
          } else {
            // Продолжаем опрашивать
            setTimeout(checkStatus, 2000)
          }
        } catch (e) {
          console.error('Error checking task status:', e)
          setAnalyzing(prev => ({ ...prev, [chapterId]: false }))
        }
      }
      
      checkStatus()
    } catch (e) {
      console.error('Error starting analysis:', e)
      alert('Ошибка запуска анализа')
      setAnalyzing(prev => ({ ...prev, [chapterId]: false }))
    }
  }

  if (loading) return <div>Загрузка глав...</div>

  return (
    <div>
      <h3>Главы проекта</h3>
      
      {/* Форма создания главы */}
      <form onSubmit={createChapter} style={{ marginBottom: 24, padding: 16, border: '1px solid #ddd', borderRadius: 8 }}>
        <h4>Добавить главу</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <input
            value={newChapter.title}
            onChange={(e) => setNewChapter(prev => ({ ...prev, title: e.target.value }))}
            placeholder="Название главы"
            style={{ padding: 8 }}
          />
          <textarea
            value={newChapter.original_text}
            onChange={(e) => setNewChapter(prev => ({ ...prev, original_text: e.target.value }))}
            placeholder="Оригинальный текст главы"
            rows={5}
            style={{ padding: 8, resize: 'vertical' }}
          />
          <button type="submit" style={{ padding: 8, alignSelf: 'flex-start' }}>
            Добавить главу
          </button>
        </div>
      </form>

      {/* Список глав */}
      {chapters.length === 0 ? (
        <p>Главы отсутствуют. Добавьте первую главу.</p>
      ) : (
        <div style={{ display: 'grid', gap: 16 }}>
          {chapters.map((chapter) => (
            <div 
              key={chapter.id} 
              style={{ 
                border: '1px solid #ddd', 
                padding: 16, 
                borderRadius: 8 
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <h4 style={{ margin: '0 0 8px 0' }}>{chapter.title}</h4>
                  <div style={{ fontSize: '0.9em', color: '#666', marginBottom: 8 }}>
                    Символов: {chapter.original_text.length}
                  </div>
                  <div style={{ 
                    maxHeight: 100, 
                    overflow: 'hidden', 
                    fontSize: '0.9em',
                    color: '#666',
                    fontStyle: 'italic'
                  }}>
                    {chapter.original_text.substring(0, 200)}...
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: 8 }}>
                  <button 
                    onClick={() => analyzeChapter(chapter.id)}
                    disabled={analyzing[chapter.id]}
                    style={{ 
                      padding: '8px 16px', 
                      fontSize: '0.9em',
                      backgroundColor: analyzing[chapter.id] ? '#ccc' : '#2196F3',
                      color: 'white',
                      border: 'none',
                      borderRadius: 4
                    }}
                  >
                    {analyzing[chapter.id] ? 'Анализ...' : 'Анализировать'}
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
