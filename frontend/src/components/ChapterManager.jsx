import React, { useState, useEffect, useRef } from 'react'
import api from '@/services/apiClient'
import { Modal } from '@/components/ui/Modal'
import { Textarea } from '@/components/ui/Textarea'
import { Spinner } from '@/components/ui/Spinner'
import { Terminal, FileText, CheckCircle2, Eye, Plus, Languages, Trash2, Upload, Activity, AlertTriangle, FileCode } from 'lucide-react'

export default function ChapterManager({ projectId }) {
  const [chapters, setChapters] = useState([])
  const [loading, setLoading] = useState(false)
  const [newChapter, setNewChapter] = useState({ title: '', original_text: '' })
  const [previewData, setPreviewData] = useState(null)
  const [uploadingChapters, setUploadingChapters] = useState(false)
  // Removed unused active state dictionaries in favor of chapter status
  const [chapterPattern, setChapterPattern] = useState('Глава \\d+')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  // Derived state for active processing to trigger polling
  const hasActiveTasks = chapters.some(ch =>
    ['pending', 'extracting', 'relationships', 'summarizing', 'translating'].includes(ch.analysis_status) ||
    ['pending', 'translating'].includes(ch.translation_status)
  );

  const getStatusLabel = (status) => {
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
  }

  const loadChapters = async () => {
    // Only show full loading spinner on first load
    if (chapters.length === 0) setLoading(true)
    try {
      const res = await api.get(`/projects/${projectId}/chapters`, { params: { sort_by: 'order', order: 'asc' } })
      setChapters(res.data)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => {
    if (projectId) loadChapters()
  }, [projectId])

  // Polling for active tasks
  useEffect(() => {
    let interval;
    if (hasActiveTasks) {
      interval = setInterval(loadChapters, 3000);
    }
    return () => clearInterval(interval);
  }, [hasActiveTasks, projectId]);

  const createChapter = async () => {
    if (!newChapter.title.trim() || !newChapter.original_text.trim()) return
    try {
      await api.post(`/projects/${projectId}/chapters`, newChapter)
      setNewChapter({ title: '', original_text: '' })
      setIsCreateModalOpen(false)
      loadChapters()
    } catch (e) { alert('ERROR: WRITE_FAILED') }
  }

  const deleteChapter = async (chapterId) => {
    if (!confirm('CONFIRM_DELETION_SEQUENCE?')) return
    try {
      await api.delete(`/projects/chapters/${chapterId}`)
      loadChapters()
    } catch (e) { alert('ERROR: DELETE_FAILED') }
  }

  const uploadChaptersFromFile = async (fileToUpload) => {
    if (!fileToUpload) return;
    setUploadingChapters(true);
    if (!chapterPattern) {
      alert("PATTERN_ERROR: MISSING_INPUT")
      setUploadingChapters(false)
      return;
    }
    console.log("DEBUG: Uploading with pattern:", chapterPattern)
    try {
      const formData = new FormData()
      formData.append('file', fileToUpload)
      formData.append('chapter_pattern', chapterPattern)
      const res = await api.post(`/projects/${projectId}/upload_chapters`, formData)
      alert(`UPLOAD COMPLETE: ${res.data.chapters_created} FILES CREATED`)
      loadChapters()
    } catch (e) {
      console.error(e)
      alert('UPLOAD FAILURE')
    } finally { setUploadingChapters(false) }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      uploadChaptersFromFile(file);
    }
  }

  const analyzeChapter = async (chapterId) => {
    try {
      await api.post(`/processing/chapters/${chapterId}/analyze-async`)
      // Optimistic update to trigger polling
      setChapters(prev => prev.map(ch => ch.id === chapterId ? { ...ch, analysis_status: 'pending' } : ch))
    } catch (e) { alert('INIT FAIL') }
  }

  const translateChapter = async (chapterId) => {
    try {
      await api.post(`/translation/chapters/${chapterId}/translate-async`)
      // Optimistic update
      setChapters(prev => prev.map(ch => ch.id === chapterId ? { ...ch, translation_status: 'pending' } : ch))
    } catch (e) { alert('INIT FAIL') }
  }

  const previewTranslation = async (chapterId) => {
    try {
      const res = await api.get(`/translation/chapters/${chapterId}/translation-preview`)
      setPreviewData(res.data)
    } catch (e) { alert('Preview Error') }
  }

  return (
    <div className="space-y-6 font-mono text-sm max-w-[1200px] mx-auto">
      {/* Controls */}
      <div className="flex flex-col md:flex-row justify-between items-end border-b border-accent/20 pb-4 gap-4">
        <div>
          <div className="text-[10px] text-muted-foreground mb-1 tracking-widest uppercase">Current_Directory</div>
          <div className="text-xl text-accent font-bold flex items-center tracking-tighter shadow-accent">
            <span className="mr-2 text-secondary-accent">/ROOT/CHAPTERS/</span>
            <span className="animate-pulse">_</span>
          </div>
        </div>
        <div className="flex gap-4 items-center">
          <div className="group flex items-center gap-2 border-b border-accent/30 p-1 bg-surface/50 hover:border-accent transition-colors">
            <input
              className="bg-transparent border-none text-xs w-32 px-2 focus:outline-none placeholder:text-muted-foreground text-text font-bold"
              value={chapterPattern}
              onChange={(e) => setChapterPattern(e.target.value)}
              placeholder="REGEX_PATTERN..."
            />
            <label className={`flex items-center px-4 py-1 bg-accent/10 hover:bg-accent text-accent hover:text-bg transition-all uppercase text-[10px] font-bold cursor-pointer tracking-wider ${uploadingChapters ? 'opacity-50 cursor-not-allowed' : ''}`}>
              {uploadingChapters ? <Spinner className="w-3 h-3 mr-2" /> : <Upload className="w-3 h-3 mr-2" />}
              {uploadingChapters ? 'UPLOADING...' : 'UPLOAD_BATCH'}
              <input type="file" className="hidden" onChange={handleFileSelect} disabled={uploadingChapters} />
            </label>
          </div>
          <button onClick={() => setIsCreateModalOpen(true)} className="flex items-center px-6 py-2 bg-accent text-bg hover:bg-secondary-accent transition-colors uppercase text-[10px] tracking-widest font-bold shadow-[0_0_10px_rgba(0,243,255,0.3)]">
            <Plus className="w-3 h-3 mr-2" />
            NEW_FILE
          </button>
        </div>
      </div>

      {/* File List */}
      <div className="border border-accent/30 bg-surface/20 min-h-[400px] relative">
        {/* Decorative Grid Lines */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(0,243,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(0,243,255,0.02)_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

        <div className="grid grid-cols-12 gap-4 p-3 border-b border-accent/20 text-[10px] text-accent/70 bg-surface/80 font-bold tracking-widest relative z-10 uppercase">
          <div className="col-span-1">ID_Tag</div>
          <div className="col-span-4">Filename</div>
          <div className="col-span-2">Size_B</div>
          <div className="col-span-2">Process_Status</div>
          <div className="col-span-3 text-right">Execute</div>
        </div>

        {loading ? (
          <div className="p-24 flex flex-col items-center justify-center text-accent animate-pulse">
            <Activity className="w-8 h-8 mb-4" />
            <div className="tracking-widest text-xs">SCANNING_SECTOR_DATA...</div>
          </div>
        ) : (
          <div className="divide-y divide-accent/5 relative z-10">
            {chapters.map((chapter, idx) => {
              const isProcessing = ['pending', 'extracting', 'relationships', 'summarizing', 'translating'].includes(chapter.analysis_status) || ['pending', 'translating'].includes(chapter.translation_status);

              let processingStatus = chapter.translation_status;
              if (['pending', 'extracting', 'relationships', 'summarizing'].includes(chapter.analysis_status)) {
                processingStatus = chapter.analysis_status;
              } else if (chapter.analysis_status === 'completed' && !chapter.translated_text && chapter.translation_status === 'idle') {
                processingStatus = 'analyzed';
              } else if (['pending', 'translating'].includes(chapter.translation_status)) {
                processingStatus = chapter.translation_status;
              }

              return (
                <div key={chapter.id} className="grid grid-cols-12 gap-4 p-3 items-center transition-all duration-300 group border border-transparent hover:border-accent hover:bg-surface/60 hover:shadow-[0_0_15px_rgba(0,243,255,0.15)] relative overflow-hidden">
                  <div className="absolute inset-0 bg-accent/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                  <div className="col-span-1 text-muted-foreground text-[10px] font-mono opacity-50 group-hover:text-accent transition-colors relative z-10">{String(idx + 1).padStart(3, '0')}</div>
                  <div className="col-span-4 font-bold text-text truncate flex items-center relative z-10">
                    <FileCode className="w-3 h-3 mr-3 text-secondary-accent opacity-50 group-hover:opacity-100" />
                    <span className="group-hover:text-accent group-hover:translate-x-1 transition-all duration-300">{chapter.title}</span>
                  </div>
                  <div className="col-span-2 text-[10px] text-muted-foreground font-mono relative z-10">{(chapter.original_text || '').length.toLocaleString()}</div>
                  <div className="col-span-2 relative z-10">
                    {isProcessing ? (
                      <span className="text-secondary-accent text-[10px] flex items-center animate-pulse tracking-widest">
                        <Spinner className="w-3 h-3 mr-2" />
                        {getStatusLabel(processingStatus)}
                      </span>
                    ) : processingStatus === 'analyzed' ? (
                      <span className="text-blue-400 text-[10px] flex items-center tracking-widest shadow-[0_0_10px_rgba(96,165,250,0.3)]">
                        <CheckCircle2 className="w-3 h-3 mr-2" /> ANALYZED
                      </span>
                    ) : chapter.translated_text ? (
                      <span className="text-accent text-[10px] flex items-center tracking-widest shadow-accent"><CheckCircle2 className="w-3 h-3 mr-2" /> READY</span>
                    ) : (
                      <span className="text-muted-foreground text-[10px] opacity-30 tracking-widest">PENDING</span>
                    )}
                  </div>
                  <div className="col-span-3 flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0 duration-200 relative z-10">
                    <ActionButton onClick={() => analyzeChapter(chapter.id)} icon={Activity} label="ANALYZE" />
                    <ActionButton onClick={() => translateChapter(chapter.id)} icon={Languages} label="TRANSLATE" />
                    <ActionButton onClick={() => previewTranslation(chapter.id)} icon={Eye} label="VIEW" />
                    <ActionButton onClick={() => deleteChapter(chapter.id)} icon={Trash2} label="PURGE" variant="destructive" />
                  </div>
                </div>
              )
            })}
            {chapters.length === 0 && (
              <div className="p-16 text-center text-muted-foreground border-t border-accent/10 border-dashed flex flex-col items-center">
                <AlertTriangle className="w-8 h-8 mb-4 opacity-50" />
                <span className="tracking-widest text-xs">NO_FILES_FOUND. INITIATE UPLOAD OR CREATE NEW FILE.</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Modal - Custom Neon Style */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm">
          <div className="w-full max-w-lg border-2 border-accent bg-bg p-1 relative shadow-[0_0_50px_rgba(0,243,255,0.2)]">
            {/* Corners */}
            <div className="absolute top-0 left-0 w-4 h-4 border-t-4 border-l-4 border-accent" />
            <div className="absolute top-0 right-0 w-4 h-4 border-t-4 border-r-4 border-accent" />
            <div className="absolute bottom-0 left-0 w-4 h-4 border-b-4 border-l-4 border-accent" />
            <div className="absolute bottom-0 right-0 w-4 h-4 border-b-4 border-r-4 border-accent" />

            <div className="p-6 bg-surface/90">
              <h3 className="text-accent text-lg font-bold mb-6 flex items-center tracking-widest uppercase">
                <Terminal className="w-5 h-5 mr-2" />
                NEW_CHAPTER_ENTRY
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-[10px] text-accent/70 uppercase tracking-widest block mb-1">Filename / Title</label>
                  <input
                    className="w-full bg-bg border-b border-accent/50 p-2 text-text focus:border-accent focus:outline-none font-bold"
                    value={newChapter.title}
                    onChange={(e) => setNewChapter(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="CHAPTER_01..."
                    autoFocus
                  />
                </div>
                <div>
                  <label className="text-[10px] text-accent/70 uppercase tracking-widest block mb-1">Content Data</label>
                  <Textarea
                    className="w-full h-40 bg-bg border border-accent/20 p-2 text-text focus:border-accent focus:outline-none resize-none font-mono text-xs"
                    value={newChapter.original_text}
                    onChange={(e) => setNewChapter(prev => ({ ...prev, original_text: e.target.value }))}
                    placeholder="PASTE_TEXT_DATA..."
                  />
                </div>
              </div>
              <div className="flex justify-end gap-4 mt-8">
                <button onClick={() => setIsCreateModalOpen(false)} className="text-muted-foreground hover:text-destructive px-4 py-2 uppercase text-[10px] font-bold tracking-widest transition-colors">ABORT</button>
                <button onClick={createChapter} className="bg-accent text-bg px-6 py-2 uppercase text-[10px] font-bold hover:bg-white transition-colors tracking-widest shadow-[0_0_15px_rgba(0,243,255,0.4)]">EXECUTE_WRITE</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <Modal
        isOpen={!!previewData}
        onClose={() => setPreviewData(null)}
        title="DATA_PREVIEW"
        className="max-w-4xl border-accent"
      >
        {previewData && (
          <div className="grid grid-cols-2 gap-4 h-[60vh]">
            <div className="border border-border bg-bg/50 p-4 overflow-auto font-mono text-xs text-muted-foreground whitespace-pre-wrap">{previewData.original_text}</div>
            <div className="border border-accent/30 bg-accent/5 p-4 overflow-auto font-mono text-xs text-text whitespace-pre-wrap shadow-inner">{previewData.translated_text}</div>
          </div>
        )}
      </Modal>
    </div>
  )
}

const ActionButton = ({ onClick, icon: Icon, label, variant = 'default' }) => (
  <button
    onClick={onClick}
    title={label}
    className={`
            p-2 transition-all duration-200 border border-transparent
            ${variant === 'destructive'
        ? 'hover:text-destructive hover:border-destructive/30 hover:bg-destructive/10'
        : 'hover:text-accent hover:border-accent/30 hover:bg-accent/10'
      }
        `}
  >
    <Icon className="w-4 h-4" />
  </button>
);
