import { useState, useEffect, useCallback, useRef } from 'react'
import api from '@/services/apiClient'

export function useChapterManager(projectId) {
  const [chapters, setChapters] = useState([])
  const chaptersRef = useRef(chapters)
  useEffect(() => { chaptersRef.current = chapters }, [chapters])

  const [loading, setLoading] = useState(false)
  const [newChapter, setNewChapter] = useState({ title: '', original_text: '' })
  const [previewData, setPreviewData] = useState(null)
  const [uploadingChapters, setUploadingChapters] = useState(false)
  const [creating, setCreating] = useState(false)
  // Removed unused active state dictionaries in favor of chapter status
  const [chapterPattern, setChapterPattern] = useState('Глава \\d+')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  const [error, setError] = useState(null) // New error state

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') setIsCreateModalOpen(false)
    }
    if (isCreateModalOpen) {
      window.addEventListener('keydown', handleEsc)
    }
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isCreateModalOpen])

  // Derived state for active processing to trigger polling
  const hasActiveTasks = chapters.some(ch =>
    ['pending', 'extracting', 'relationships', 'summarizing', 'translating'].includes(ch.analysis_status) ||
    ['pending', 'translating'].includes(ch.translation_status)
  );

  const getStatusLabel = useCallback((status) => {
    switch (status) {
      case 'pending': return 'PENDING'
      case 'extracting': return 'EXTRACTING'
      case 'relationships': return 'NET_ANALYSIS'
      case 'summarizing': return 'SUMMARIZING'
      case 'translating': return 'TRANSLATING'
      case 'analyzed': return 'ANALYZED'
      case 'completed': return 'COMPLETED'
      case 'failed': return 'FAILED'
      default: return status?.toUpperCase() || ''
    }
  }, [])

  const loadChapters = useCallback(async () => {
    // Only show full loading spinner on first load
    if (chaptersRef.current.length === 0) setLoading(true)
    setError(null)
    try {
      const res = await api.get(`/projects/${projectId}/chapters`, { params: { sort_by: 'order', order: 'asc' } })
      setChapters(res.data)
    } catch (e) {
      console.error(e)
      setError("CONNECTION_ERROR: FAILED_TO_FETCH_DATA")
    } finally { setLoading(false) }
  }, [projectId])

  useEffect(() => {
    if (projectId) loadChapters()
  }, [projectId, loadChapters])

  // Polling for active tasks
  useEffect(() => {
    let interval;
    if (hasActiveTasks) {
      interval = setInterval(loadChapters, 3000);
    }
    return () => clearInterval(interval);
  }, [hasActiveTasks, projectId, loadChapters]);

  const createChapter = async (e) => {
    if (e) e.preventDefault()
    if (!newChapter.title.trim() || !newChapter.original_text.trim()) return
    setError(null)
    setCreating(true)
    try {
      await api.post(`/projects/${projectId}/chapters`, newChapter)
      setNewChapter({ title: '', original_text: '' })
      setIsCreateModalOpen(false)
      loadChapters()
    } catch (e) {
      setError('WRITE_ERROR: FAILED_TO_CREATE_CHAPTER')
    } finally {
      setCreating(false)
    }
  }

  const deleteChapter = async (chapterId) => {
    if (!confirm('CONFIRM_DELETION_SEQUENCE?')) return
    setError(null)
    try {
      await api.delete(`/projects/chapters/${chapterId}`)
      loadChapters()
    } catch (e) { setError('DELETE_ERROR: FAILED_TO_REMOVE_FILE') }
  }

  const uploadChaptersFromFile = async (fileToUpload) => {
    if (!fileToUpload) return;
    setUploadingChapters(true);
    setError(null)
    if (!chapterPattern) {
      setError("PATTERN_ERROR: MISSING_INPUT")
      setUploadingChapters(false)
      return;
    }
    console.log("DEBUG: Uploading with pattern:", chapterPattern)
    try {
      const formData = new FormData()
      formData.append('file', fileToUpload)
      formData.append('chapter_pattern', chapterPattern)
      const res = await api.post(`/projects/${projectId}/upload_chapters`, formData)
      alert(`UPLOAD COMPLETE: ${res.data.chapters_created} FILES CREATED`) // Keep success alert or change to toast? Keeping for now as per plan focus on errors.
      loadChapters()
    } catch (e) {
      console.error(e)
      setError('UPLOAD_FAILURE: CHECK_FILE_FORMAT_OR_PATTERN')
    } finally { setUploadingChapters(false) }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      uploadChaptersFromFile(file);
    }
    e.target.value = null; // FIX: Reset input so same file can be selected again
  }

  const analyzeChapter = async (chapterId) => {
    setError(null)
    try {
      await api.post(`/processing/chapters/${chapterId}/analyze-async`)
      // Optimistic update to trigger polling
      setChapters(prev => prev.map(ch => ch.id === chapterId ? { ...ch, analysis_status: 'pending' } : ch))
    } catch (e) { setError('INIT_FAIL: ANALYSIS_SEQUENCE_ABORTED') }
  }

  const translateChapter = async (chapterId) => {
    setError(null)
    try {
      await api.post(`/translation/chapters/${chapterId}/translate-async`)
      // Optimistic update
      setChapters(prev => prev.map(ch => ch.id === chapterId ? { ...ch, translation_status: 'pending' } : ch))
    } catch (e) { setError('INIT_FAIL: TRANSLATION_SEQUENCE_ABORTED') }
  }

  const previewTranslation = async (chapterId) => {
    setError(null)
    try {
      const res = await api.get(`/translation/chapters/${chapterId}/translation-preview`)
      setPreviewData(res.data)
    } catch (e) { setError('PREVIEW_ERROR: DATA_CORRUPTION_OR_MISSING') }
  }

  return {
    chapters,
    loading,
    newChapter,
    setNewChapter,
    previewData,
    setPreviewData,
    uploadingChapters,
    creating,
    chapterPattern,
    setChapterPattern,
    isCreateModalOpen,
    setIsCreateModalOpen,
    error,
    setError,
    getStatusLabel,
    createChapter,
    deleteChapter,
    handleFileSelect,
    analyzeChapter,
    translateChapter,
    previewTranslation
  }
}
