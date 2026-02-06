import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Home, Book, FileText, Share2, Languages, History, Layers, ArrowLeft, Loader2, Sparkles, ChevronRight } from 'lucide-react';

// Modules
import ChapterManager from '@/components/ChapterManager.jsx';
import GlossaryEditor from '@/components/GlossaryEditor.jsx';
import RelationshipsViewer from '@/components/RelationshipsViewer.jsx';
import { AetherReader } from './AetherReader.jsx';
import GlossaryVersionManager from '@/components/GlossaryVersionManager.jsx';
import BatchProcessor from '@/components/BatchProcessor.jsx';

export function AetherProjectPage({ project, loading, projectId }) {
    const [activeTab, setActiveTab] = useState('chapters');

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
                <div className="relative">
                    <div className="absolute inset-0 bg-accent/30 blur-xl rounded-full animate-pulse" />
                    <Loader2 className="w-12 h-12 text-accent animate-spin relative z-10" />
                </div>
                <div className="text-slate-500 font-heading tracking-widest text-sm animate-pulse">
                    CONJURING PROJECT DATA...
                </div>
            </div>
        );
    }

    if (!project) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
                <h2 className="text-2xl font-bold text-slate-800 mb-2">Project Not Found</h2>
                <Link to="/" className="text-accent hover:underline">Return to Library</Link>
            </div>
        );
    }

    const tabs = [
        { id: 'chapters', label: 'Chapters', icon: Book },
        { id: 'glossary', label: 'Glossary', icon: FileText },
        { id: 'relationships', label: 'Relations', icon: Share2 },
        { id: 'translations', label: 'Translations', icon: Languages },
        { id: 'versions', label: 'History', icon: History },
        { id: 'batch', label: 'Batch', icon: Layers },
    ];

    return (
        <div className="space-y-8 animate-fade-in pb-20 max-w-7xl mx-auto">
            {/* Header Island */}
            <div className="bg-white/40 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-xl relative overflow-hidden group">
                {/* Background Decor */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-300/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />

                <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div>
                        <Link to="/" className="inline-flex items-center text-sm font-bold text-slate-500 hover:text-accent transition-colors mb-3 uppercase tracking-wider group-hover:-translate-x-1 duration-300">
                            <ArrowLeft className="w-4 h-4 mr-1" />
                            Library
                        </Link>
                        <h1 className="text-4xl md:text-5xl font-heading font-bold text-slate-800 tracking-tight drop-shadow-sm flex items-center gap-3">
                            {project.name}
                            <Sparkles className="w-6 h-6 text-accent opacity-50 group-hover:opacity-100 transition-opacity animate-pulse" />
                        </h1>
                        <div className="flex items-center gap-4 mt-3 text-sm font-medium text-slate-600">
                            <span className="bg-white/50 px-3 py-1 rounded-full border border-white/60 shadow-sm uppercase tracking-wide text-xs">
                                {project.genre}
                            </span>
                            <span className="flex items-center gap-1 opacity-70">
                                <ClockIcon /> Created {new Date(project.created_at).toLocaleDateString()}
                            </span>
                        </div>
                    </div>

                    {/* Status Orb */}
                    <div className="hidden md:flex flex-col items-center">
                        <div className="w-16 h-16 rounded-full bg-white/40 border border-white/60 shadow-inner flex items-center justify-center relative">
                            <div className="absolute inset-0 bg-accent/20 rounded-full animate-ping opacity-20" />
                            <div className="w-3 h-3 bg-accent rounded-full shadow-[0_0_10px_theme(colors.accent.DEFAULT)]" />
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-2">Active</span>
                    </div>
                </div>
            </div>

            {/* Navigation Dock */}
            <div className="sticky top-4 z-40 flex justify-center">
                <div className="bg-white/70 backdrop-blur-xl border border-white/40 shadow-2xl rounded-full p-1.5 flex items-center gap-1 overflow-x-auto max-w-full custom-scrollbar-hide">
                    {tabs.map(tab => {
                        const Icon = tab.icon;
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`
                                    flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-bold transition-all duration-300 whitespace-nowrap
                                    ${isActive
                                        ? 'bg-accent text-white shadow-lg shadow-accent/25 scale-105'
                                        : 'text-slate-500 hover:bg-white/50 hover:text-slate-700'
                                    }
                                `}
                            >
                                <Icon className={`w-4 h-4 ${isActive ? 'animate-bounce-short' : ''}`} />
                                {tab.label}
                            </button>
                        )
                    })}
                </div>
            </div>

            {/* Content Island */}
            <div className="bg-white/30 backdrop-blur-md border border-white/40 rounded-3xl p-6 md:p-8 shadow-xl min-h-[600px] transition-all duration-500">
                <div className={`transition-opacity duration-300 ${loading ? 'opacity-50' : 'opacity-100'}`}>
                    {activeTab === 'chapters' && <ChapterManager projectId={projectId} />}
                    {activeTab === 'glossary' && <GlossaryEditor projectId={projectId} />}
                    {activeTab === 'relationships' && <RelationshipsViewer projectId={projectId} />}
                    {activeTab === 'translations' && <AetherReader projectId={projectId} />}
                    {activeTab === 'versions' && <GlossaryVersionManager projectId={projectId} />}
                    {activeTab === 'batch' && <BatchProcessor projectId={projectId} />}
                </div>
            </div>

            <style>{`
                /* Override internal components for Glass Theme */
                .card, .bg-card, .bg-background {
                    background-color: rgba(255, 255, 255, 0.4) !important;
                    backdrop-filter: blur(8px);
                    border: 1px solid rgba(255, 255, 255, 0.4) !important;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
                }
                .text-card-foreground {
                    color: #334155 !important;
                }
                .border-border {
                    border-color: rgba(255, 255, 255, 0.5) !important;
                }
                /* Hide scrollbar for nav */
                .custom-scrollbar-hide::-webkit-scrollbar {
                    display: none;
                }
                .custom-scrollbar-hide {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }
                @keyframes bounce-short {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-20%); }
                }
                .animate-bounce-short {
                    animation: bounce-short 0.5s ease-in-out;
                }
            `}</style>
        </div>
    );
}

const ClockIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
    </svg>
)
