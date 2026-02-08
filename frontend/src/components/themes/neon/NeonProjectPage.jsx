import React, { useState, useEffect, useId } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Book, Share2, Languages, History, Layers, FileText, Cpu, Database, Edit2, Activity, ShieldCheck, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Spinner } from '@/components/ui/Spinner'
import api from '@/services/apiClient'

import ChapterManager from '@/components/ChapterManager.jsx'
import ChapterViewer from '@/components/ChapterViewer.jsx'
import GlossaryEditor from '@/components/GlossaryEditor.jsx'
import RelationshipsViewer from '@/components/RelationshipsViewer.jsx'
import BatchProcessor from '@/components/BatchProcessor.jsx'
import GlossaryVersionManager from '@/components/GlossaryVersionManager.jsx'

export function NeonProjectPage({ project, loading, projectId, onRefresh }) {
  const [activeModule, setActiveModule] = useState('chapters')
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [editFormData, setEditFormData] = useState({ name: '', genre: '' })
  const [updating, setUpdating] = useState(false)

  const openEditModal = () => {
    setEditFormData({ name: project.name, genre: project.genre || '' })
    setIsEditModalOpen(true)
  }

  const handleUpdateProject = async () => {
    if (!editFormData.name.trim()) return
    setUpdating(true)
    try {
      await api.put(`/projects/${projectId}`, editFormData)
      await onRefresh()
      setIsEditModalOpen(false)
    } catch (e) {
      console.error('Error updating project:', e)
      alert('Failed to update project')
    } finally {
      setUpdating(false)
    }
  }

  if (loading) return (
    <div className="flex h-[50vh] items-center justify-center font-mono">
      <div className="flex flex-col items-center">
        <Activity className="w-12 h-12 text-accent animate-spin mb-4" />
        <span className="text-secondary-accent tracking-widest animate-pulse">ESTABLISHING_UPLINK...</span>
      </div>
    </div>
  )

  if (!project) return <div className="text-center py-24 text-destructive font-mono text-xl border border-destructive/50 bg-destructive/10">ERROR: NULL_TARGGET_DATA</div>

  const modules = [
    { id: 'chapters', label: 'CHAPTER_LOG', icon: Book },
    { id: 'glossary', label: 'GLOSSARY_DB', icon: FileText },
    { id: 'relationships', label: 'RELATIONS_NET', icon: Share2 },
    { id: 'translations', label: 'TRANSLATION_VIEW', icon: Languages },
    { id: 'versions', label: 'BACKUP_VERSIONS', icon: History },
    { id: 'batch', label: 'BATCH_PROCESS', icon: Layers },
  ]

  return (
    <div className="space-y-6 font-mono text-sm max-w-[1600px] mx-auto p-4">
      {/* Mission Briefing Header */}
      <header className="border-b border-accent/30 pb-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 opacity-10">
          <Cpu className="w-64 h-64 text-accent animate-pulse" />
        </div>

        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 relative z-10">
          <div className="space-y-4 w-full md:w-auto">
            <Link to="/" className="group flex items-center text-xs text-text-muted hover:text-accent transition-colors w-fit">
              <ArrowLeft className="w-3 h-3 mr-2 group-hover:-translate-x-1 transition-transform" />
              <span className="tracking-widest">RETURN_ROOT_DIR</span>
            </Link>

            <div className="flex items-center gap-4">
              <div className="w-2 h-12 bg-accent shadow-[0_0_15px_rgba(0,243,255,0.5)]" />
              <div>
                <div className="text-[10px] text-secondary-accent uppercase tracking-[0.2em] mb-1">Target Designation</div>
                <h1 className="text-4xl font-bold text-text uppercase tracking-tighter flex items-center shadow-accent">
                  {project.name}
                  <button onClick={openEditModal} className="ml-4 text-text-muted hover:text-accent transition-colors opacity-50 hover:opacity-100">
                    <Edit2 className="w-5 h-5" />
                  </button>
                </h1>
              </div>
            </div>
          </div>

          {/* HUD Stats Grid */}
          <div className="grid grid-cols-3 gap-1 bg-surface/50 border border-border p-1">
            <HudStat label="GENRE_CLASS" value={project.genre} icon={<Database className="w-3 h-3" />} />
            <HudStat label="SEC_LEVEL" value="ALPHA" icon={<ShieldCheck className="w-3 h-3 text-secondary-accent" />} />
            <HudStat label="STATUS" value="ACTIVE" icon={<Activity className="w-3 h-3 text-accent" />} />
          </div>
        </div>
      </header>

      {/* Navigation Modules (Tabs) */}
      <nav className="flex flex-wrap gap-2 pt-2">
        {modules.map(mod => {
          const Icon = mod.icon;
          const isActive = activeModule === mod.id;
          return (
            <button
              key={mod.id}
              onClick={() => setActiveModule(mod.id)}
              className={`
                                flex items-center px-6 py-3 text-xs font-bold uppercase tracking-widest transition-all relative overflow-hidden group
                                ${isActive
                  ? 'text-bg bg-accent clip-path-tech'
                  : 'text-text-muted hover:text-accent border border-accent/20 hover:border-accent/60 bg-surface/20 hover:bg-surface/50 clip-path-tech'
                }
                            `}
            >
              <div className={`absolute inset-0 bg-secondary-accent/20 transform -skew-x-12 translate-x-[-150%] group-hover:translate-x-[150%] transition-transform duration-700 ${isActive ? 'hidden' : 'block'}`} />
              <Icon className="w-4 h-4 mr-3" />
              {mod.label}
            </button>
          )
        })}
      </nav>

      {/* Main Content Viewport */}
      <main className="min-h-[600px] border-2 border-accent/10 bg-surface/30 backdrop-blur-sm relative p-1">
        {/* Tech Corners */}
        <div className="absolute -top-[2px] -left-[2px] w-4 h-4 border-t-2 border-l-2 border-accent" />
        <div className="absolute -top-[2px] -right-[2px] w-4 h-4 border-t-2 border-r-2 border-accent" />
        <div className="absolute -bottom-[2px] -left-[2px] w-4 h-4 border-b-2 border-l-2 border-accent" />
        <div className="absolute -bottom-[2px] -right-[2px] w-4 h-4 border-b-2 border-r-2 border-accent" />

        {/* Scanline Effect */}
        <div className="absolute inset-0 bg-scanline pointer-events-none opacity-5" />

        <div className="p-6 relative z-10">
          {activeModule === 'chapters' && <ChapterManager projectId={projectId} />}
          {activeModule === 'glossary' && <NeonWrapper><GlossaryEditor projectId={projectId} /></NeonWrapper>}
          {activeModule === 'relationships' && <NeonWrapper><RelationshipsViewer projectId={projectId} /></NeonWrapper>}
          {activeModule === 'translations' && <ChapterViewer projectId={projectId} />}
          {activeModule === 'versions' && <NeonWrapper><GlossaryVersionManager projectId={projectId} /></NeonWrapper>}
          {activeModule === 'batch' && <NeonWrapper><BatchProcessor projectId={projectId} /></NeonWrapper>}
        </div>
      </main>

      {/* Global Styles for transparent overrides */}
      <style>{`
                .clip-path-tech {
                    clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
                }
                .neon-force-transparent .card,
                .neon-force-transparent .bg-card,
                .neon-force-transparent .bg-background {
                    background-color: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                }
                .neon-force-transparent table {
                    border-collapse: separate;
                    border-spacing: 0 2px;
                }
                .neon-force-transparent th {
                    background-color: rgba(0, 243, 255, 0.05) !important;
                    color: var(--color-accent) !important;
                    font-family: 'Space Mono', monospace;
                    text-transform: uppercase;
                    font-size: 0.7rem;
                    letter-spacing: 0.1em;
                    border-bottom: 1px solid var(--color-accent);
                    padding: 12px !important;
                }
                .neon-force-transparent td {
                    font-family: 'Space Mono', monospace;
                    font-size: 0.8rem;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                    padding: 12px !important;
                    color: var(--color-text-muted);
                }
                .neon-force-transparent tr:hover td {
                    background-color: rgba(0, 243, 255, 0.05);
                    color: var(--color-text);
                }
            `}</style>

      {/* Edit Modal */}
      <NeonModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="MODIFY_TARGET_PARAMETERS"
      >
        <div className="space-y-6 font-mono">
          <div className="space-y-2">
            <Label htmlFor="edit-name" className="text-[10px] uppercase text-accent tracking-widest">Designation</Label>
            <Input
              id="edit-name"
              value={editFormData.name}
              onChange={(e) => setEditFormData(prev => ({ ...prev, name: e.target.value }))}
              className="bg-bg/50 border-accent/30 text-text font-bold text-lg h-12 focus:border-accent"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-genre" className="text-[10px] uppercase text-accent tracking-widest">Classification</Label>
            <Input
              id="edit-genre"
              value={editFormData.genre}
              onChange={(e) => setEditFormData(prev => ({ ...prev, genre: e.target.value }))}
              className="bg-bg/50 border-accent/30 text-text h-12 focus:border-accent"
              list="neon-genre-options"
            />
            <datalist id="neon-genre-options">
              <option value="wuxia" />
              <option value="xianxia" />
              <option value="litrpg" />
              <option value="scifi" />
              <option value="fantasy" />
            </datalist>
          </div>
          <div className="flex justify-end gap-4 pt-6 mt-4 border-t border-accent/10">
            <Button
              variant="ghost"
              onClick={() => setIsEditModalOpen(false)}
              disabled={updating}
              className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 uppercase tracking-wider"
            >
              ABORT_SEQUENCE
            </Button>
            <Button
              onClick={handleUpdateProject}
              disabled={updating}
              className="bg-accent text-bg hover:bg-secondary-accent font-bold uppercase tracking-wider min-w-[140px]"
            >
              {updating ? <Spinner className="mr-2 h-4 w-4" /> : <ShieldCheck className="w-4 h-4 mr-2" />}
              COMMIT
            </Button>
          </div>
        </div>
      </NeonModal>
    </div>
  )
}

// Helper Components
const HudStat = ({ label, value, icon }) => (
  <div className="flex flex-col items-center justify-center p-2 bg-bg hover:bg-surface transition-colors cursor-default">
    <div className="text-[10px] text-text-muted uppercase mb-1 flex items-center gap-1">
      {icon} {label}
    </div>
    <div className="text-secondary-accent font-bold text-sm uppercase tracking-wider">{value}</div>
  </div>
);

const NeonWrapper = ({ children }) => (
  <div className="neon-force-transparent">
    {children}
  </div>
);

const NeonModal = ({ isOpen, onClose, title, children }) => {
  const titleId = useId();

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="w-full max-w-lg border border-accent bg-surface/95 relative shadow-[0_0_50px_rgba(0,243,255,0.2)]"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <div className="flex items-center justify-between p-4 border-b border-accent/20 bg-accent/5">
          <h3
            id={titleId}
            className="text-accent font-bold uppercase tracking-widest flex items-center"
          >
            <AlertCircle className="w-4 h-4 mr-2" /> {title}
          </h3>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-destructive transition-colors text-xl font-bold"
            aria-label="Close"
          >
            &times;
          </button>
        </div>
        <div className="p-6">
          {children}
        </div>
        {/* Corner Accents */}
        <div className="absolute top-0 left-0 w-2 h-2 bg-accent" />
        <div className="absolute top-0 right-0 w-2 h-2 bg-accent" />
        <div className="absolute bottom-0 left-0 w-2 h-2 bg-accent" />
        <div className="absolute bottom-0 right-0 w-2 h-2 bg-accent" />
      </div>
    </div>
  );
};
