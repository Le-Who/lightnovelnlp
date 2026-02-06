import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Book, Share2, Languages, History, Layers, FileText, Cpu, Database } from 'lucide-react'
import api from '@/services/apiClient'
import { NeonChapterManager } from './NeonChapterManager'
import { NeonReader } from './NeonReader'
import GlossaryEditor from '@/components/GlossaryEditor.jsx'
import RelationshipsViewer from '@/components/RelationshipsViewer.jsx'
import BatchProcessor from '@/components/BatchProcessor.jsx'
import GlossaryVersionManager from '@/components/GlossaryVersionManager.jsx'
import ChapterViewer from '@/components/ChapterViewer.jsx'

export function NeonProjectPage() {
    const { projectId } = useParams()
    const [project, setProject] = useState(null)
    const [loading, setLoading] = useState(false)
    const [activeModule, setActiveModule] = useState('chapters')

    const loadProject = async () => {
        setLoading(true)
        try {
            const res = await api.get(`/projects/${projectId}`)
            setProject(res.data)
        } catch (e) { console.error(e) } finally { setLoading(false) }
    }

    useEffect(() => { if (projectId) loadProject() }, [projectId])

    if (loading) return <div className="flex h-[50vh] items-center justify-center text-accent animate-pulse font-mono">LOADING_PROJECT_DATA...</div>
    if (!project) return <div className="text-center py-12 text-destructive font-mono">ERROR: PROJECT_NOT_FOUND</div>

    const modules = [
        { id: 'chapters', label: 'CHAPTER_LOG', icon: Book },
        { id: 'glossary', label: 'GLOSSARY_DB', icon: FileText },
        { id: 'relationships', label: 'RELATIONS_NET', icon: Share2 },
        { id: 'translations', label: 'TRANSLATION_VIEW', icon: Languages },
        { id: 'versions', label: 'BACKUP_VERSIONS', icon: History },
        { id: 'batch', label: 'BATCH_PROCESS', icon: Layers },
    ]

    return (
        <div className="space-y-6 font-mono text-sm max-w-[1400px] mx-auto">
            {/* Header Info */}
            <div className="flex items-center justify-between border-b border-accent/20 pb-4">
                <div className="flex items-center gap-4">
                    <Link to="/" className="text-muted-foreground hover:text-accent transition-colors flex items-center text-xs uppercase tracking-widest">
                        <ArrowLeft className="w-3 h-3 mr-1" /> RETURN_ROOT
                    </Link>
                    <div className="h-6 w-[1px] bg-accent/20" />
                    <div>
                        <h1 className="text-2xl font-bold text-accent tracking-tighter uppercase flex items-center">
                            <Cpu className="w-5 h-5 mr-3 animate-pulse" />
                            {project.name}
                        </h1>
                        <div className="flex gap-4 text-[10px] text-muted-foreground mt-1">
                            <span>ID: {project.id}</span>
                            <span>GENRE: {project.genre.toUpperCase()}</span>
                            <span>CREATED: {new Date(project.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
                <div className="text-right hidden md:block">
                    <div className="text-[10px] text-accent">SYSTEM_STATUS</div>
                    <div className="text-xl font-bold">ONLINE</div>
                </div>
            </div>

            {/* Navigation Modules (Tabs) */}
            <div className="flex flex-wrap gap-2 border-b-2 border-accent/10 pb-1">
                {modules.map(mod => {
                    const Icon = mod.icon;
                    const isActive = activeModule === mod.id;
                    return (
                        <button
                            key={mod.id}
                            onClick={() => setActiveModule(mod.id)}
                            className={`
                        flex items-center px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all
                        ${isActive
                                    ? 'bg-accent text-bg shadow-[0_0_15px_rgba(0,255,148,0.3)] clip-path-slant'
                                    : 'bg-surface/50 text-muted-foreground hover:text-accent hover:bg-accent/10'
                                }
                    `}
                            style={{ clipPath: 'polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)' }}
                        >
                            <Icon className="w-3 h-3 mr-2" />
                            {mod.label}
                        </button>
                    )
                })}
            </div>

            {/* Content Area */}
            <div className="border border-accent/10 bg-surface/10 p-4 relative min-h-[600px]">
                {/* Decorative Corner Brackets */}
                <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-accent opacity-50" />
                <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-accent opacity-50" />
                <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-accent opacity-50" />
                <div className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-accent opacity-50" />

                {activeModule === 'chapters' && <NeonChapterManager projectId={projectId} />}
                {activeModule === 'glossary' && <div className="neon-wrapper"><GlossaryEditor projectId={projectId} /></div>}
                {activeModule === 'relationships' && <div className="neon-wrapper"><RelationshipsViewer projectId={projectId} /></div>}
                {activeModule === 'translations' && <NeonReader projectId={projectId} />}
                {activeModule === 'versions' && <div className="neon-wrapper"><GlossaryVersionManager projectId={projectId} /></div>}
                {activeModule === 'batch' && <div className="neon-wrapper"><BatchProcessor projectId={projectId} /></div>}
            </div>

            <style>{`
          /* Quick CSS override for nested components to force transparent backgrounds */
          .neon-wrapper .card, 
          .neon-wrapper .bg-card, 
          .neon-wrapper .bg-background {
              background-color: transparent !important;
              border: none !important;
              box-shadow: none !important;
          }
          .neon-wrapper table {
              border-collapse: separate;
              border-spacing: 0 4px;
          }
          .neon-wrapper th {
              background-color: rgba(0, 255, 148, 0.1) !important;
              color: var(--color-accent) !important;
              font-family: monospace;
              text-transform: uppercase;
              font-size: 0.75rem;
          }
          .neon-wrapper td {
              font-family: monospace;
              font-size: 0.8rem;
              border-bottom: 1px solid rgba(0, 255, 148, 0.1);
          }
          /* Custom Scrollbar for Neon pages */
          .custom-scrollbar::-webkit-scrollbar {
              width: 8px;
              height: 8px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
              background: rgba(0, 255, 148, 0.05);
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
              background: rgba(0, 255, 148, 0.3);
              border-radius: 0;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
              background: rgba(0, 255, 148, 0.6);
          }
      `}</style>
        </div>
    )
}
