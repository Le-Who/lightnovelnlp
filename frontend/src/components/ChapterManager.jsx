import React, { useState, useEffect, useRef } from 'react'
import api from '../services/apiClient'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { Textarea } from './ui/Textarea'
import { Badge } from './ui/Badge'
import { Label } from './ui/Label'
import { Modal } from './ui/Modal'
import { Spinner } from './ui/Spinner'
import { Alert } from './ui/Alert'
import { Upload, FileText, CheckCircle2, Eye, Plus, Languages, AlertCircle, Trash2 } from 'lucide-react'

export default function ChapterManager({ projectId }) {
  const [chapters, setChapters] = useState([])
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState({})  // chapterId -> status string
  const [translating, setTranslating] = useState({})  // chapterId -> status string
  const [newChapter, setNewChapter] = useState({ title: '', original_text: '' })
  const [previewData, setPreviewData] = useState(null)
  const [uploadingChapters, setUploadingChapters] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [chapterPattern, setChapterPattern] = useState('Глава \\d+')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const modalRef = useRef(null)

  // Status mapping
  const getStatusLabel = (status) => {
    switch (status) {
      case 'pending': return 'Ожидание...'
      case 'extracting': return 'Извлечение терминов...'
      case 'relationships': return 'Анализ связей...'
      case 'summarizing': return 'Создание саммари...'
      case 'translating': return 'Перевод...'
      case 'completed': return 'Завершено!'
      case 'failed': return 'Ошибка'
      default: return status
    }
  }

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

  const createChapter = async () => {
    if (!newChapter.title.trim() || !newChapter.original_text.trim()) return

    try {
      await api.post(`/projects/${projectId}/chapters`, newChapter)
      setNewChapter({ title: '', original_text: '' })
      setIsCreateModalOpen(false)
      loadChapters()
    } catch (e) {
      console.error('Error creating chapter:', e)
      alert('Ошибка создания главы')
    }
  }

  const deleteChapter = async (chapterId) => {
    if (!confirm('Вы уверены, что хотите удалить эту главу?')) return

    try {
      await api.delete(`/projects/${projectId}/chapters/${chapterId}`)
      loadChapters()
    } catch (e) {
      console.error('Error deleting chapter:', e)
      alert('Ошибка удаления главы')
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
      loadChapters() // Reload list
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
    setAnalyzing(prev => ({ ...prev, [chapterId]: 'pending' }))

    try {
      await api.post(`/processing/chapters/${chapterId}/analyze-async`)

      const pollStatus = async () => {
        try {
          const statusRes = await api.get(`/processing/chapters/${chapterId}/status`)
          const status = statusRes.data.analysis_status

          setAnalyzing(prev => ({ ...prev, [chapterId]: status }))

          if (status === 'completed') {
            loadChapters()
            setTimeout(() => {
              setAnalyzing(prev => ({ ...prev, [chapterId]: null }))
            }, 1000)
          } else if (status === 'failed') {
            setAnalyzing(prev => ({ ...prev, [chapterId]: null }))
            alert(`Ошибка анализа: ${statusRes.data.analysis_error || 'Неизвестная ошибка'}`)
          } else {
            setTimeout(pollStatus, 2000)
          }
        } catch (e) {
          console.error('Error polling status:', e)
          setAnalyzing(prev => ({ ...prev, [chapterId]: null }))
        }
      }

      setTimeout(pollStatus, 500)

    } catch (e) {
      console.error('Error starting analysis:', e)
      setAnalyzing(prev => ({ ...prev, [chapterId]: null }))
      alert('Ошибка запуска анализа')
    }
  }

  const translateChapter = async (chapterId) => {
    setTranslating(prev => ({ ...prev, [chapterId]: 'pending' }))

    try {
      await api.post(`/translation/chapters/${chapterId}/translate-async`)

      const pollStatus = async () => {
        try {
          const statusRes = await api.get(`/processing/chapters/${chapterId}/status`)
          const status = statusRes.data.translation_status

          setTranslating(prev => ({ ...prev, [chapterId]: status }))

          if (status === 'completed') {
            loadChapters()
            setTimeout(() => {
              setTranslating(prev => ({ ...prev, [chapterId]: null }))
            }, 1000)
          } else if (status === 'failed') {
            setTranslating(prev => ({ ...prev, [chapterId]: null }))
            alert(`Ошибка перевода: ${statusRes.data.translation_error || 'Неизвестная ошибка'}`)
          } else {
            setTimeout(pollStatus, 2000)
          }
        } catch (e) {
          console.error('Error polling status:', e)
          setTranslating(prev => ({ ...prev, [chapterId]: null }))
        }
      }

      setTimeout(pollStatus, 500)

    } catch (e) {
      console.error('Error starting translation:', e)
      setTranslating(prev => ({ ...prev, [chapterId]: null }))
      alert('Ошибка перевода')
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

  useEffect(() => {
    if (previewData && modalRef.current) {
      modalRef.current.focus()
    }
  }, [previewData])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && previewData) {
        setPreviewData(null)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [previewData])

  if (loading) return <div>Загрузка глав...</div>

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <h3 className="text-xl font-semibold text-slate-900">Главы проекта</h3>
        <div className="flex gap-2">
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Добавить главу
          </Button>
        </div>
      </div>

      {/* Загрузка глав из файла */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Загрузить главы из файла</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
            <div className="space-y-2">
              <Label htmlFor="chapter-pattern">Паттерн разделения глав</Label>
              <Input
                id="chapter-pattern"
                value={chapterPattern}
                onChange={(e) => setChapterPattern(e.target.value)}
                placeholder="Глава \\d+"
              />
              <p className="text-xs text-slate-500">
                Регулярное выражение для разделения (по умолчанию: "Глава \\d+")
              </p>
            </div>

            <div className="flex gap-2 items-center">
              <Input
                type="file"
                accept=".txt"
                onChange={handleFileSelect}
                className="cursor-pointer"
              />
              <Button
                onClick={uploadChaptersFromFile}
                disabled={uploadingChapters || !selectedFile}
                className="whitespace-nowrap"
              >
                {uploadingChapters ? <Spinner className="w-4 h-4 mr-2" /> : <Upload className="h-4 w-4 mr-2" />}
                Загрузить
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Список глав */}
      {chapters.length === 0 ? (
        <Alert>
          Главы отсутствуют. Добавьте первую главу вручную или загрузите из файла.
        </Alert>
      ) : (
        <div className="space-y-4">
          {chapters.map((chapter) => (
            <Card key={chapter.id}>
              <CardContent className="p-4 md:p-6">
                <div className="flex flex-col md:flex-row gap-4 justify-between">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-lg font-medium text-slate-900">{chapter.title}</h4>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteChapter(chapter.id)}
                        className="h-8 w-8 text-slate-400 hover:text-red-600 md:hidden"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-slate-500">
                      <span className="flex items-center gap-1">
                        <FileText className="h-4 w-4" />
                        {chapter.original_text.length} симв.
                      </span>
                      {chapter.translated_text && (
                        <Badge variant="success" className="gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          Переведено
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-slate-600 line-clamp-2">
                      {chapter.original_text}
                    </p>
                  </div>

                  <div className="flex flex-row md:flex-col gap-2 items-stretch md:w-48">
                    <Button
                      onClick={() => analyzeChapter(chapter.id)}
                      disabled={!!analyzing[chapter.id]}
                      variant={analyzing[chapter.id] ? "secondary" : "default"}
                      className="flex-1"
                    >
                      {analyzing[chapter.id] ? (
                        <>
                          <Spinner className="w-4 h-4 mr-2" />
                          {getStatusLabel(analyzing[chapter.id])}
                        </>
                      ) : (
                        "Анализировать"
                      )}
                    </Button>

                    <Button
                      onClick={() => previewTranslation(chapter.id)}
                      variant="outline"
                      className="flex-1"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Предпросмотр
                    </Button>

                    <Button
                      onClick={() => translateChapter(chapter.id)}
                      disabled={!!translating[chapter.id]}
                      variant={translating[chapter.id] ? "secondary" : "default"}
                      className={`flex-1 ${!translating[chapter.id] && 'bg-green-600 hover:bg-green-700'}`}
                    >
                      {translating[chapter.id] ? (
                        <>
                          <Spinner className="w-4 h-4 mr-2" />
                          {getStatusLabel(translating[chapter.id])}
                        </>
                      ) : (
                        <>
                          <Languages className="w-4 h-4 mr-2" />
                          Перевести
                        </>
                      )}
                    </Button>

                    <Button
                      variant="ghost"
                      onClick={() => deleteChapter(chapter.id)}
                      className="hidden md:flex text-slate-400 hover:text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Удалить
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Модальное окно создания главы */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Добавить новую главу"
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="chapter-title">Название главы</Label>
            <Input
              id="chapter-title"
              value={newChapter.title}
              onChange={(e) => setNewChapter(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Как называется глава"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="chapter-text">Текст главы</Label>
            <Textarea
              id="chapter-text"
              value={newChapter.original_text}
              onChange={(e) => setNewChapter(prev => ({ ...prev, original_text: e.target.value }))}
              placeholder="Вставьте текст главы сюда..."
              className="min-h-[200px]"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>
              Отмена
            </Button>
            <Button onClick={createChapter}>
              Создать главу
            </Button>
          </div>
        </div>
      </Modal>

      {/* Модальное окно предварительного просмотра */}
      <Modal
        isOpen={!!previewData}
        onClose={closePreview}
        title="Предварительный просмотр перевода"
        className="max-w-4xl"
      >
        {previewData?.preview_available ? (
          <div className="space-y-4 h-[70vh] flex flex-col">
            <div>
              <strong>Использовано терминов глоссария:</strong> {previewData.glossary_terms_count}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 overflow-hidden">
              <div className="flex flex-col h-full">
                <h4 className="font-medium mb-2">Оригинал</h4>
                <div className="border rounded-md p-4 bg-slate-50 overflow-auto flex-1 text-sm whitespace-pre-wrap">
                  {previewData.original_text}
                </div>
              </div>

              <div className="flex flex-col h-full">
                <h4 className="font-medium mb-2">Перевод</h4>
                <div className="border rounded-md p-4 bg-white overflow-auto flex-1 text-sm whitespace-pre-wrap">
                  {previewData.translated_text}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-red-500 p-4">
            {previewData?.message}
          </div>
        )}
      </Modal>
    </div>
  )
}
