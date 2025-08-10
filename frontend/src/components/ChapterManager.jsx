import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'

export default function ChapterManager({ projectId }) {
  const [chapters, setChapters] = useState([])
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState({})
  const [translating, setTranslating] = useState({})
  const [newChapter, setNewChapter] = useState({ title: '', original_text: '' })
  const [previewData, setPreviewData] = useState(null)
  const [uploadingChapters, setUploadingChapters] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [chapterPattern, setChapterPattern] = useState('Глава \\d+')

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
      await api.post(`/projects/${projectId}/chapters`, newChapter)
      setNewChapter({ title: '', original_text: '' })
      loadChapters()
    } catch (e) {
      console.error('Error creating chapter:', e)
      alert('Ошибка создания главы')
    }
  }

  const uploadChaptersFromFile = async () => {
    if (!selectedFile) {
      alert('Пожалуйста, выберите файл')
      return
    }

    setUploadingChapters(true)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('chapter_pattern', chapterPattern)

      const res = await api.post(`/projects/${projectId}/upload_chapters`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      alert(`Успешно загружено ${res.data.chapters_created} глав!`)
      setSelectedFile(null)
      loadChapters() // Перезагружаем список глав
    } catch (e) {
      console.error('Error uploading chapters:', e)
      if (e.response?.data?.detail) {
        alert(`Ошибка загрузки: ${e.response.data.detail}`)
      } else {
        alert('Ошибка загрузки глав')
      }
    } finally {
      setUploadingChapters(false)
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'text/plain') {
      setSelectedFile(file)
    } else {
      alert('Пожалуйста, выберите текстовый файл (.txt)')
      e.target.value = ''
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

  const translateChapter = async (chapterId) => {
    setTranslating(prev => ({ ...prev, [chapterId]: true }))
    
    try {
      const res = await api.post(`/translation/chapters/${chapterId}/translate`)
      alert(`Перевод завершен! Использовано терминов: ${res.data.glossary_terms_used}`)
      loadChapters() // Перезагружаем для обновления перевода
    } catch (e) {
      console.error('Error translating chapter:', e)
      if (e.response?.data?.detail) {
        alert(`Ошибка перевода: ${e.response.data.detail}`)
      } else {
        alert('Ошибка перевода')
      }
    } finally {
      setTranslating(prev => ({ ...prev, [chapterId]: false }))
    }
  }

  const previewTranslation = async (chapterId) => {
    try {
      const res = await api.get(`/translation/chapters/${chapterId}/translation-preview`)
      setPreviewData(res.data)
    } catch (e) {
      console.error('Error getting preview:', e)
      alert('Ошибка получения предварительного просмотра')
    }
  }

  const closePreview = () => {
    setPreviewData(null)
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

      {/* Загрузка глав из файла */}
      <div style={{ marginBottom: 24, padding: 16, border: '1px solid #ddd', borderRadius: 8 }}>
        <h4>Загрузить главы из файла</h4>
        <div style={{ marginBottom: 10 }}>
          <label style={{ display: 'block', marginBottom: 5 }}>
            Паттерн разделения глав:
          </label>
          <input
            type="text"
            value={chapterPattern}
            onChange={(e) => setChapterPattern(e.target.value)}
            placeholder="Глава \\d+"
            style={{ 
              width: '100%', 
              padding: '8px', 
              border: '1px solid #ddd', 
              borderRadius: 4,
              marginBottom: 10
            }}
          />
          <small style={{ color: '#666' }}>
            Используйте регулярное выражение для разделения глав (по умолчанию: "Глава \\d+")
          </small>
        </div>
        <input
          type="file"
          accept=".txt"
          onChange={handleFileSelect}
          style={{ marginBottom: 10 }}
        />
        <button 
          onClick={uploadChaptersFromFile} 
          disabled={uploadingChapters || !selectedFile}
          style={{
            padding: '8px 16px',
            backgroundColor: uploadingChapters ? '#ccc' : '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: 4,
            cursor: uploadingChapters ? 'not-allowed' : 'pointer'
          }}
        >
          {uploadingChapters ? 'Загрузка...' : 'Загрузить главы из файла'}
        </button>
      </div>

      {/* Список глав */}
      {chapters.length === 0 ? (
        <p>Главы отсутствуют. Добавьте первую главу или загрузите из файла.</p>
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
                    {chapter.translated_text && (
                      <span style={{ marginLeft: 16, color: '#4CAF50' }}>
                        ✓ Переведено
                      </span>
                    )}
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
                
                <div style={{ display: 'flex', gap: 8, flexDirection: 'column' }}>
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
                  
                  <button 
                    onClick={() => previewTranslation(chapter.id)}
                    style={{ 
                      padding: '8px 16px', 
                      fontSize: '0.9em',
                      backgroundColor: '#FF9800',
                      color: 'white',
                      border: 'none',
                      borderRadius: 4
                    }}
                  >
                    Предварительный просмотр
                  </button>
                  
                  <button 
                    onClick={() => translateChapter(chapter.id)}
                    disabled={translating[chapter.id]}
                    style={{ 
                      padding: '8px 16px', 
                      fontSize: '0.9em',
                      backgroundColor: translating[chapter.id] ? '#ccc' : '#4CAF50',
                      color: 'white',
                      border: 'none',
                      borderRadius: 4
                    }}
                  >
                    {translating[chapter.id] ? 'Перевод...' : 'Перевести'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Модальное окно предварительного просмотра */}
      {previewData && (
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
            maxWidth: '80%',
            maxHeight: '80%',
            overflow: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3>Предварительный просмотр перевода</h3>
              <button onClick={closePreview} style={{ padding: '8px 16px', border: 'none', backgroundColor: '#f44336', color: 'white', borderRadius: 4 }}>
                ✕
              </button>
            </div>
            
            {previewData.preview_available ? (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <strong>Использовано терминов глоссария:</strong> {previewData.glossary_terms_count}
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div>
                    <h4>Оригинал</h4>
                    <div style={{ 
                      border: '1px solid #ddd', 
                      padding: 16, 
                      borderRadius: 4,
                      maxHeight: 400,
                      overflow: 'auto',
                      fontSize: '0.9em'
                    }}>
                      {previewData.original_text}
                    </div>
                  </div>
                  
                  <div>
                    <h4>Перевод</h4>
                    <div style={{ 
                      border: '1px solid #ddd', 
                      padding: 16, 
                      borderRadius: 4,
                      maxHeight: 400,
                      overflow: 'auto',
                      fontSize: '0.9em'
                    }}>
                      {previewData.translated_text}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ color: '#f44336' }}>
                {previewData.message}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
