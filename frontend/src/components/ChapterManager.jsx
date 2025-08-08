import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'

export default function ChapterManager({ projectId }) {
  const [chapters, setChapters] = useState([])
  const [loading, setLoading] = useState(false)

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

  if (loading) return <div>Загрузка глав...</div>

  return (
    <div>
      <h3>Главы проекта</h3>
      {chapters.length === 0 ? (
        <p>Главы отсутствуют</p>
      ) : (
        <div>
          {chapters.map(chapter => (
            <div key={chapter.id} style={{ marginBottom: 16, padding: 16, border: '1px solid #ddd', borderRadius: 8 }}>
              <h4>{chapter.title}</h4>
              <p>Статус: {chapter.summary ? 'Проанализирована' : 'Не проанализирована'}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
