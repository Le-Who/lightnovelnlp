import React, { useState, useEffect } from 'react'
import api from '@/services/apiClient'
import { Terminal, FileText, ArrowRight, Eye, MessageSquare, X, Maximize2, Minimize2, ChevronLeft, ChevronRight } from 'lucide-react'
import { Spinner } from '@/components/ui/Spinner'

export function NeonReader({ projectId }) {
    const [chapters, setChapters] = useState([])
    const [loading, setLoading] = useState(false)
    const [selectedChapter, setSelectedChapter] = useState(null)
    const [isFullScreen, setIsFullScreen] = useState(false)

    const loadChapters = async () => {
        setLoading(true)
        try {
            const res = await api.get(`/projects/${projectId}/chapters`, { params: { sort_by: 'order', order: 'asc' } })
            setChapters(res.data.filter(ch => ch.translated_text))
        } catch (e) { console.error(e) } finally { setLoading(false) }
    }

    useEffect(() => { if (projectId) loadChapters() }, [projectId])

    if (loading) return <div className="p-12 text-center text-accent animate-pulse">LOADING_READER_MODULE...</div>

    // Reader View
    if (selectedChapter) {
        return (
            <div className={`flex flex-col h-full ${isFullScreen ? 'fixed inset-0 z-50 bg-bg p-4' : 'min-h-[600px]'}`}>
                {/* Reader Toolbar */}
                <div className="flex justify-between items-center border-b border-accent/30 pb-2 mb-4 bg-surface/50 p-2">
                    <div className="flex items-center gap-4">
                        <button onClick={() => setSelectedChapter(null)} className="flex items-center text-muted-foreground hover:text-accent font-bold uppercase text-xs">
                            <ChevronLeft className="w-4 h-4 mr-1" /> BACK_TO_LIST
                        </button>
                        <div className="h-4 w-[1px] bg-accent/20" />
                        <div className="text-accent font-bold text-sm tracking-wider flex items-center">
                            <FileText className="w-4 h-4 mr-2" />
                            {selectedChapter.title}
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => setIsFullScreen(!isFullScreen)} className="text-accent hover:text-white p-1">
                            {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                        </button>
                    </div>
                </div>

                {/* Split View */}
                <div className="flex-1 flex flex-col md:flex-row gap-4 min-h-0 overflow-hidden">
                    {/* Original Panel */}
                    <div className="flex-1 min-h-0 flex flex-col border border-accent/20 bg-surface/10 relative group">
                        <div className="absolute top-0 left-0 bg-accent/10 px-2 py-1 text-[10px] text-accent font-bold uppercase border-b border-r border-accent/20">SOURCE_DATA</div>
                        <div className="flex-1 overflow-auto p-6 pt-8 font-mono text-xs md:text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed custom-scrollbar">
                            {selectedChapter.original_text}
                        </div>
                    </div>

                    {/* Translation Panel */}
                    <div className="flex-1 min-h-0 flex flex-col border border-accent/50 bg-surface/20 relative shadow-[0_0_20px_rgba(0,255,148,0.05)]">
                        <div className="absolute top-0 left-0 bg-accent text-bg px-2 py-1 text-[10px] font-bold uppercase">COMPILED_OUTPUT</div>
                        <div className="flex-1 overflow-auto p-6 pt-8 font-mono text-xs md:text-sm text-text whitespace-pre-wrap leading-relaxed custom-scrollbar relative">
                            {/* Scanline effect */}
                            <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%),linear-gradient(90deg,rgba(255,0,0,0.03),rgba(0,255,0,0.01),rgba(0,0,255,0.03))] z-0 pointer-events-none bg-[length:100%_4px,3px_100%]" />
                            <div className="relative z-10">
                                {selectedChapter.translated_text}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    // List View
    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-accent font-bold uppercase tracking-widest flex items-center">
                    <Eye className="w-4 h-4 mr-2" />
                    AVAILABLE_TRANSLATIONS
                </h3>
                <div className="text-[10px] text-muted-foreground">COUNT: {chapters.length}</div>
            </div>

            {chapters.length === 0 ? (
                <div className="border border-dashed border-accent/20 p-12 text-center text-muted-foreground">
                    NO_TRANSLATED_DATA_FOUND. INITIATE_TRANSLATION_SEQUENCE.
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {chapters.map(chapter => (
                        <div
                            key={chapter.id}
                            onClick={() => setSelectedChapter(chapter)}
                            className="border border-accent/20 bg-surface/30 p-4 cursor-pointer hover:bg-accent/10 hover:border-accent transition-all group relative overflow-hidden"
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div className="font-bold text-text group-hover:text-accent truncate pr-4">{chapter.title}</div>
                                <ArrowRight className="w-4 h-4 text-accent opacity-0 group-hover:opacity-100 transition-opacity transform -translate-x-2 group-hover:translate-x-0" />
                            </div>
                            <div className="text-[10px] text-muted-foreground font-mono flex gap-4 mt-4">
                                <span>SRC: {chapter.original_text.length}B</span>
                                <span>OUT: {chapter.translated_text.length}B</span>
                            </div>

                            {/* Decorative corner */}
                            <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-accent opacity-50 group-hover:opacity-100" />
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
