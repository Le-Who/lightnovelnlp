import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'

export default function ChapterViewer({ projectId }) {
  const [chapters, setChapters] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedChapter, setSelectedChapter] = useState(null)
  const [reviewing, setReviewing] = useState({})
  const [reviewData, setReviewData] = useState({})

  const loadChapters = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/projects/${projectId}/chapters`, {
        params: {
          sort_by: 'order',
          order: 'asc'
        }
      })
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

  const requestReview = async (chapterId) => {
    setReviewing(prev => ({ ...prev, [chapterId]: true }))
    try {
      const res = await api.post(`/translation/chapters/${chapterId}/review`)
      if (res.data.review_available) {
        setReviewData(prev => ({ ...prev, [chapterId]: res.data.review_text }))
        alert('Рецензирование завершено!')
      } else {
        alert('Ошибка рецензирования: ' + res.data.message)
      }
    } catch (e) {
      console.error('Error requesting review:', e)
      alert('Ошибка запроса рецензирования')
    } finally {
      setReviewing(prev => ({ ...prev, [chapterId]: false }))
    }
  }

  if (loading) return <div>Загрузка глав...</div>

  const translatedChapters = chapters.filter(ch => ch.translated_text)

  return (
    <div>
      <h3>Переведенные главы</h3>
      
      {translatedChapters.length === 0 ? (
        <p>Переведенные главы отсутствуют. Сначала переведите главы в разделе "Главы".</p>
      ) : (
        <div style={{ display: 'grid', gap: 16 }}>
          {translatedChapters.map((chapter) => (
            <div 
              key={chapter.id} 
              style={{ 
                border: '1px solid #ddd', 
                padding: 16, 
                borderRadius: 8,
                cursor: 'pointer'
              }}
              onClick={() => setSelectedChapter(chapter)}
            >
              <h4 style={{ margin: '0 0 8px 0' }}>{chapter.title}</h4>
              <div style={{ fontSize: '0.9em', color: '#666', marginBottom: 8 }}>
                Символов: {chapter.original_text.length} → {chapter.translated_text.length}
              </div>
              
              {/* Кнопка рецензирования */}
              <div style={{ marginBottom: 8 }}>
                <button 
                  onClick={(e) => {
                    e.stopPropagation()
                    requestReview(chapter.id)
                  }}
                  disabled={reviewing[chapter.id]}
                  style={{ 
                    padding: '6px 12px', 
                    fontSize: '0.8em',
                    backgroundColor: reviewing[chapter.id] ? '#ccc' : '#9C27B0',
                    color: 'white',
                    border: 'none',
                    borderRadius: 4,
                    cursor: reviewing[chapter.id] ? 'not-allowed' : 'pointer'
                  }}
                >
                  {reviewing[chapter.id] ? 'Рецензирование...' : 'Рецензировать перевод'}
                </button>
              </div>
              <div style={{ 
                maxHeight: 100, 
                overflow: 'hidden', 
                fontSize: '0.9em',
                color: '#666',
                fontStyle: 'italic'
              }}>
                {chapter.translated_text.substring(0, 200)}...
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Модальное окно просмотра главы */}
      {selectedChapter && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: 24,
            borderRadius: 8,
            maxWidth: '90%',
            maxHeight: '90%',
            overflow: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3>{selectedChapter.title}</h3>
              <button 
                onClick={() => setSelectedChapter(null)} 
                style={{ padding: '8px 16px', border: 'none', backgroundColor: '#f44336', color: 'white', borderRadius: 4 }}
              >
                ✕
              </button>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
              <div>
                <h4>Оригинал</h4>
                <div style={{ 
                  border: '1px solid #ddd', 
                  padding: 16, 
                  borderRadius: 4,
                  maxHeight: 600,
                  overflow: 'auto',
                  fontSize: '0.9em',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap'
                }}>
                  {selectedChapter.original_text}
                </div>
              </div>
              
              <div>
                <h4>Перевод</h4>
                <div style={{ 
                  border: '1px solid #ddd', 
                  padding: 16, 
                  borderRadius: 4,
                  maxHeight: 600,
                  overflow: 'auto',
                  fontSize: '0.9em',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap'
                }}>
                  {selectedChapter.translated_text}
                </div>
              </div>
            </div>
            
            {/* Кнопки действий */}
            <div style={{ marginTop: 24, display: 'flex', gap: 16 }}>
              {!reviewData[selectedChapter.id] && (
                <button 
                  onClick={() => requestReview(selectedChapter.id)}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#2196F3',
                    color: 'white',
                    border: 'none',
                    borderRadius: 4,
                    cursor: 'pointer'
                  }}
                >
                  Запросить рецензию
                </button>
              )}
            </div>
            
            {/* Рецензия перевода */}
            {reviewData[selectedChapter.id] && (
              <div style={{ marginTop: 24 }}>
                <h4>Рецензия перевода</h4>
                <div style={{ 
                  border: '1px solid #ddd', 
                  padding: 16, 
                  borderRadius: 4,
                  maxHeight: 400,
                  overflow: 'auto',
                  fontSize: '0.9em',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                  backgroundColor: '#f9f9f9'
                }}>
                  {reviewData[selectedChapter.id]}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
