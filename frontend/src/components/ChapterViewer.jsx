import React, { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import api from '@/services/apiClient'
import { Terminal, FileText, ArrowRight, Eye, Maximize2, Minimize2, ChevronLeft, ChevronRight, Hash, Download } from 'lucide-react'
import { Spinner } from '@/components/ui/Spinner'

export default function ChapterViewer({ projectId }) {
  const [chapters, setChapters] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedChapter, setSelectedChapter] = useState(null)
  const [isFullScreen, setIsFullScreen] = useState(false)
  const [loadingChapter, setLoadingChapter] = useState(false)

  const loadChapters = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/projects/${projectId}/chapters`, { params: { sort_by: 'order', order: 'asc' } })
      setChapters(res.data.filter(ch => (ch.translated_text_length || 0) > 0))
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { if (projectId) loadChapters() }, [projectId])

  // Effect to handle ESC key for full screen
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && isFullScreen) setIsFullScreen(false)
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isFullScreen])

  const handleSelectChapter = async (chapter) => {
    if (selectedChapter?.id === chapter.id) return
    setLoadingChapter(true)
    try {
      const res = await api.get(`/projects/chapters/${chapter.id}`)
      setSelectedChapter(res.data)
    } catch (e) {
      console.error("Failed to load chapter", e)
    } finally {
      setLoadingChapter(false)
    }
  }

  // Keyboard navigation for reader mode
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Only navigate if we have a chapter selected and not loading
      if (!selectedChapter || loadingChapter) return

      // Avoid interfering with inputs
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return

      // Find current index
      const currentIndex = chapters.findIndex(c => c.id === selectedChapter.id)
      if (currentIndex === -1) return

      if (e.key === 'ArrowLeft') {
        if (currentIndex > 0) handleSelectChapter(chapters[currentIndex - 1])
      } else if (e.key === 'ArrowRight') {
        if (currentIndex < chapters.length - 1) handleSelectChapter(chapters[currentIndex + 1])
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedChapter, chapters, loadingChapter])

  const downloadChapter = () => {
    if (!selectedChapter.translated_text) return;
    const blob = new Blob([selectedChapter.translated_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedChapter.title || 'chapter'}_translated.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  if (loading || loadingChapter) return (
    <div className="flex items-center justify-center p-24 text-accent animate-pulse font-mono tracking-widest text-xs">
      <Spinner className="w-6 h-6 mr-3" />
      {loading ? 'LOADING_READER_MODULE...' : 'LOADING_CHAPTER_DATA...'}
    </div>
  )

  // Reader View Content
  const readerContent = selectedChapter ? (
    <div className={`flex flex-col ${isFullScreen ? 'fixed inset-0 z-[99999] bg-bg p-0' : 'h-[800px]'} transition-all duration-300`}>
      {/* Reader Toolbar */}
      <div className={`flex justify-between items-center border-b-2 border-accent/20 bg-surface/80 shadow-[0_5px_15px_rgba(0,0,0,0.5)] backdrop-blur-md ${isFullScreen ? 'p-4' : 'p-4 mb-4'}`}>
        <div className="flex items-center gap-6">
          <button
            onClick={() => setSelectedChapter(null)}
            className="group flex items-center text-muted-foreground hover:text-accent font-bold uppercase text-[10px] tracking-widest transition-colors"
          >
            <ChevronLeft className="w-4 h-4 mr-1 group-hover:-translate-x-1 transition-transform" />
            Abort_Read
          </button>
          <div className="h-6 w-[2px] bg-accent/20" />
          <div className="flex flex-col">
            <div className="text-[10px] text-accent/50 uppercase tracking-[0.2em] mb-1">Active_File</div>
            <div className="text-text font-bold text-sm tracking-wider flex items-center shadow-accent">
              <FileText className="w-4 h-4 mr-2" />
              {selectedChapter.title}
            </div>
          </div>
        </div>
        <div className="flex gap-4 items-center">
          <div className="text-[10px] text-muted-foreground hidden md:block">
            <span className="text-secondary-accent">SRC_SIZE:</span> {selectedChapter.original_text.length}B
            <span className="mx-2">|</span>
            <span className="text-accent">OUT_SIZE:</span> {selectedChapter.translated_text.length}B
          </div>

          {/* Chapter Navigation */}
          <div className="flex items-center border border-accent/20 rounded-md overflow-hidden">
            <button
              onClick={() => {
                const idx = chapters.findIndex(c => c.id === selectedChapter.id);
                if (idx > 0) handleSelectChapter(chapters[idx - 1]);
              }}
              disabled={chapters.findIndex(c => c.id === selectedChapter.id) === 0}
              className="p-2 hover:bg-accent/10 border-r border-accent/20 disabled:opacity-30 disabled:hover:bg-transparent"
              title="Previous Chapter (←)"
              aria-label="Previous Chapter"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                const idx = chapters.findIndex(c => c.id === selectedChapter.id);
                if (idx < chapters.length - 1) handleSelectChapter(chapters[idx + 1]);
              }}
              disabled={chapters.findIndex(c => c.id === selectedChapter.id) === chapters.length - 1}
              className="p-2 hover:bg-accent/10 disabled:opacity-30 disabled:hover:bg-transparent"
              title="Next Chapter (→)"
              aria-label="Next Chapter"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={downloadChapter}
            className="text-muted-foreground hover:text-accent p-2 border border-transparent hover:border-accent/50 transition-all hover:bg-accent/10"
            title="DOWNLOAD_DATA"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="text-accent hover:text-white p-2 border border-transparent hover:border-accent/50 transition-all hover:bg-accent/10 hover:shadow-[0_0_15px_rgba(0,243,255,0.2)]"
          >
            {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Split View */}
      <div className={`flex-1 flex flex-col md:flex-row gap-6 min-h-0 overflow-hidden ${isFullScreen ? 'p-4' : ''}`}>
        {/* Original Panel */}
        <div className="flex-1 min-h-0 flex flex-col border border-accent/10 bg-[#0a0a0c] relative group">
          {/* Tech Header */}
          <div className="absolute top-0 left-0 right-0 h-8 bg-surface/50 border-b border-accent/10 flex items-center px-4 justify-between">
            <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest">Raw_Input_Stream</span>
            <div className="flex gap-1">
              <div className="w-2 h-2 rounded-full bg-red-500/20" />
              <div className="w-2 h-2 rounded-full bg-yellow-500/20" />
              <div className="w-2 h-2 rounded-full bg-green-500/20" />
            </div>
          </div>

          <div className="flex-1 overflow-auto p-6 pt-12 font-mono text-xs md:text-sm text-text-muted/60 whitespace-pre-wrap leading-relaxed custom-scrollbar selection:bg-secondary-accent/20 selection:text-secondary-accent">
            {selectedChapter.original_text}
          </div>
        </div>

        {/* Translation Panel */}
        <div className="flex-1 min-h-0 flex flex-col border border-accent/40 bg-black relative shadow-[0_0_30px_rgba(0,243,255,0.05)]">
          {/* Tech Header */}
          <div className="absolute top-0 left-0 right-0 h-8 bg-accent/5 border-b border-accent/20 flex items-center px-4 justify-between">
            <span className="text-[10px] text-accent font-bold uppercase tracking-widest flex items-center">
              <Terminal className="w-3 h-3 mr-2" />
              Compiled_Output
            </span>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-accent animate-pulse rounded-full shadow-[0_0_5px_#00f3ff]" />
              <span className="text-[8px] text-accent">LIVE</span>
            </div>
          </div>

          {/* Scanner Line Animation Container */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-20 z-0">
            <div className="w-full h-full bg-[linear-gradient(transparent_0%,rgba(0,243,255,0.1)_50%,transparent_100%)] bg-[length:100%_4px] animate-scan" />
          </div>

          <div className="flex-1 overflow-auto p-8 pt-12 font-mono text-xs md:text-sm text-text whitespace-pre-wrap leading-loose custom-scrollbar relative z-10 selection:bg-accent/30 selection:text-white">
            {selectedChapter.translated_text}
          </div>

          {/* Footer Info */}
          <div className="absolute bottom-0 left-0 right-0 h-6 bg-accent/5 border-t border-accent/10 flex items-center px-4 justify-end text-[10px] text-accent/50 font-mono">
            <span>EOF_MARKER_DETECTED</span>
          </div>
        </div>
      </div>
    </div>
  ) : null;

  if (selectedChapter) {
    return isFullScreen ? createPortal(readerContent, document.body) : readerContent;
  }

  // List View
  return (
    <div className="space-y-6 max-w-[1200px] mx-auto">
      <div className="flex items-center justify-between mb-8 border-b border-accent/20 pb-4">
        <div className="flex flex-col">
          <div className="text-[10px] text-secondary-accent uppercase tracking-widest mb-1">Module_Status</div>
          <h3 className="text-2xl text-text font-bold uppercase tracking-tighter flex items-center">
            <Eye className="w-6 h-6 mr-3 text-accent" />
            Read_Interface
          </h3>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-muted-foreground uppercase tracking-widest">Available_Files</div>
          <div className="text-3xl font-bold text-accent font-mono leading-none mt-1">{String(chapters.length).padStart(2, '0')}</div>
        </div>
      </div>

      {chapters.length === 0 ? (
        <div className="border-2 border-dashed border-accent/20 p-16 text-center">
          <Hash className="w-12 h-12 text-accent/20 mx-auto mb-4" />
          <div className="text-accent/50 tracking-widest uppercase text-sm font-bold">No_Compiled_Data_Found</div>
          <div className="text-xs text-muted-foreground mt-2">Initiate translation sequence in Chapter Manager to generate readable output.</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {chapters.map((chapter, idx) => (
            <button
              key={chapter.id}
              type="button"
              onClick={() => handleSelectChapter(chapter)}
              className="group relative w-full text-left border border-accent/20 bg-surface/40 p-6 hover:bg-accent/5 hover:border-accent transition-all duration-300 overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              {/* Hover Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-accent/10 opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="flex justify-between items-start mb-4 relative z-10">
                <div className="text-xs font-mono text-secondary-accent px-2 py-1 bg-secondary-accent/10 border border-secondary-accent/20">
                  ID_{String(idx + 1).padStart(3, '0')}
                </div>
                <ArrowRight className="w-4 h-4 text-accent opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
              </div>

              <h4 className="font-bold text-text group-hover:text-accent truncate mb-6 text-lg tracking-tight relative z-10 transition-colors">
                {chapter.title}
              </h4>

              <div className="grid grid-cols-2 gap-2 text-[10px] text-muted-foreground font-mono relative z-10 border-t border-accent/10 pt-4">
                <div className="flex flex-col">
                  <span className="uppercase opacity-50 mb-1">Source</span>
                  <span>{(chapter.original_text_length || 0).toLocaleString()}B</span>
                </div>
                <div className="flex flex-col text-right">
                  <span className="uppercase opacity-50 mb-1">Output</span>
                  <span className="text-text">{(chapter.translated_text_length || 0).toLocaleString()}B</span>
                </div>
              </div>

              {/* Decorative styles */}
              <div className="absolute bottom-0 left-0 w-full h-[2px] bg-accent/0 group-hover:bg-accent/50 transition-colors duration-500 scale-x-0 group-hover:scale-x-100 origin-left" />
              <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-accent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-accent opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
