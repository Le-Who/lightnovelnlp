import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'
import { Card } from './ui/Card'
import { Button } from './ui/Button'
import { Modal } from './ui/Modal'
import { Spinner } from './ui/Spinner'
import { MessageSquare, ArrowRight, Eye } from 'lucide-react'

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

  if (loading) return <div className="flex justify-center p-8"><Spinner /></div>

  const translatedChapters = chapters.filter(ch => ch.translated_text)

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold tracking-tight">Переведенные главы</h3>
      </div>
      
      {translatedChapters.length === 0 ? (
        <div className="text-center py-12 border border-dashed rounded-lg text-slate-500">
          Переведенные главы отсутствуют. Сначала переведите главы в разделе &quot;Главы&quot;.
        </div>
      ) : (
        <div className="grid gap-4">
          {translatedChapters.map((chapter) => (
            <Card
              key={chapter.id} 
              className="cursor-pointer hover:border-slate-300 transition-colors"
              onClick={() => setSelectedChapter(chapter)}
            >
              <div className="p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <h4 className="font-semibold text-lg">{chapter.title}</h4>
                  <div className="text-sm text-slate-500 flex gap-2 items-center">
                    <span>Символов: {chapter.original_text.length}</span>
                    <ArrowRight className="h-3 w-3" />
                    <span>{chapter.translated_text.length}</span>
                  </div>
                  <p className="text-sm text-slate-500 italic mt-1 line-clamp-1">
                    {chapter.translated_text.substring(0, 100)}...
                  </p>
                </div>

                <div className="flex gap-2">
                   <Button
                      size="sm"
                      variant="outline"
                      className="whitespace-nowrap"
                   >
                     <Eye className="mr-2 h-4 w-4" /> Читать
                   </Button>
                   <Button
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      requestReview(chapter.id)
                    }}
                    disabled={reviewing[chapter.id]}
                    variant={reviewing[chapter.id] ? "secondary" : "default"}
                    className="whitespace-nowrap"
                  >
                    {reviewing[chapter.id] ? <Spinner className="mr-2" /> : <MessageSquare className="mr-2 h-4 w-4" />}
                    {reviewing[chapter.id] ? 'Рецензирование...' : 'Рецензировать'}
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Viewer Modal */}
      <Modal
        isOpen={!!selectedChapter}
        onClose={() => setSelectedChapter(null)}
        title={selectedChapter?.title}
        className="max-w-7xl h-[90vh]"
      >
        {selectedChapter && (
          <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 min-h-0">
              <div className="flex flex-col min-h-0">
                <h4 className="font-semibold text-sm text-slate-500 uppercase mb-2">Оригинал</h4>
                <div className="flex-1 overflow-y-auto p-4 bg-slate-50 rounded-md border text-sm whitespace-pre-wrap leading-relaxed">
                  {selectedChapter.original_text}
                </div>
              </div>
              
              <div className="flex flex-col min-h-0">
                <h4 className="font-semibold text-sm text-slate-500 uppercase mb-2">Перевод</h4>
                <div className="flex-1 overflow-y-auto p-4 bg-white rounded-md border text-sm whitespace-pre-wrap leading-relaxed shadow-sm">
                  {selectedChapter.translated_text}
                </div>
              </div>
            </div>
            
            {/* Review Section */}
            {(reviewData[selectedChapter.id] || !reviewData[selectedChapter.id]) && (
               <div className="mt-4 border-t pt-4 shrink-0">
                 {!reviewData[selectedChapter.id] ? (
                    <div className="flex justify-end">
                      <Button onClick={() => requestReview(selectedChapter.id)}>
                        <MessageSquare className="mr-2 h-4 w-4" /> Запросить рецензию AI
                      </Button>
                    </div>
                 ) : (
                   <div className="max-h-40 overflow-y-auto p-4 bg-yellow-50 border border-yellow-100 rounded-md">
                     <h4 className="font-semibold text-yellow-900 mb-2 flex items-center">
                       <MessageSquare className="mr-2 h-4 w-4" /> Рецензия AI
                     </h4>
                     <p className="text-sm text-yellow-800 whitespace-pre-wrap">
                       {reviewData[selectedChapter.id]}
                     </p>
                   </div>
                 )}
               </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
