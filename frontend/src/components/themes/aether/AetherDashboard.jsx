import React, { useState } from 'react';
import { Plus, Search, Sparkles, BookOpen, Clock, ChevronRight, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export function AetherDashboard({ projects, onCreateProject, loading, creating }) {
    const [localName, setLocalName] = useState('');
    const [localGenre, setLocalGenre] = useState('');
    const [isFormOpen, setIsFormOpen] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        onCreateProject(localName, localGenre);
        setLocalName('');
        setLocalGenre('');
        setIsFormOpen(false);
    };

    return (
        <div className="space-y-12 animate-fade-in pb-20">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-center gap-6 relative z-10">
                <div className="text-center md:text-left">
                    <h1 className="text-4xl font-heading font-bold text-slate-800 drop-shadow-sm mb-2">
                        My Library
                    </h1>
                    <p className="text-slate-600 font-body">
                        Manage your translation projects in the aether.
                    </p>
                </div>

                <button
                    onClick={() => setIsFormOpen(!isFormOpen)}
                    className={`
            group relative px-6 py-3 rounded-2xl font-semibold text-white shadow-lg 
            transition-all duration-300 transform hover:-translate-y-1
            ${isFormOpen ? 'bg-slate-400 hover:bg-slate-500' : 'bg-accent hover:shadow-accent/40 hover:shadow-xl'}
          `}
                >
                    <div className="absolute inset-0 rounded-2xl bg-white/20 blur-sm opacity-0 group-hover:opacity-100 transition-opacity" />
                    <span className="relative flex items-center gap-2">
                        {isFormOpen ? 'Close Creator' : 'New Project'}
                        <Sparkles className={`w-4 h-4 ${!isFormOpen && 'animate-pulse'}`} />
                    </span>
                </button>
            </div>

            {/* Creation Form - Floating Glass Panel */}
            <div className={`
        transition-all duration-500 ease-out overflow-hidden
        ${isFormOpen ? 'max-h-96 opacity-100 scale-100' : 'max-h-0 opacity-0 scale-95'}
      `}>
                <div className="bg-white/40 backdrop-blur-xl border border-white/60 p-8 rounded-3xl shadow-xl mx-auto max-w-2xl relative overflow-hidden">
                    {/* Decorative gradients */}
                    <div className="absolute -top-10 -left-10 w-32 h-32 bg-accent/20 rounded-full blur-3xl" />
                    <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-blue-400/20 rounded-full blur-3xl" />

                    <h2 className="text-xl font-heading font-semibold text-slate-700 mb-6 relative">
                        Weave New Story
                    </h2>

                    <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4 relative">
                        <div className="flex-1 space-y-2">
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-3">
                                Title
                            </label>
                            <input
                                value={localName}
                                onChange={(e) => setLocalName(e.target.value)}
                                placeholder="The Beginning After The End..."
                                className="w-full bg-white/50 border border-white/50 rounded-2xl px-5 py-3 
                  text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:bg-white/80 transition-all font-body"
                            />
                        </div>

                        <div className="w-full md:w-48 space-y-2">
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-3">
                                Genre
                            </label>
                            <div className="relative">
                                <select
                                    value={localGenre}
                                    onChange={(e) => setLocalGenre(e.target.value)}
                                    className="w-full bg-white/50 border border-white/50 rounded-2xl px-5 py-3 
                    text-slate-800 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:bg-white/80 appearance-none cursor-pointer transition-all font-body"
                                >
                                    <option value="">Select...</option>
                                    <option value="fantasy">Fantasy</option>
                                    <option value="scifi">Sci-Fi</option>
                                    <option value="romance">Romance</option>
                                    <option value="action">Action</option>
                                </select>
                                <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none rotate-90" />
                            </div>
                        </div>

                        <button
                            disabled={creating}
                            type="submit"
                            className="mt-6 md:mt-0 md:self-end h-[50px] px-6 rounded-2xl bg-accent text-white font-bold shadow-lg 
                hover:shadow-accent/40 hover:-translate-y-1 active:translate-y-0 transition-all disabled:opacity-70 disabled:hover:translate-y-0"
                        >
                            {creating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
                        </button>
                    </form>
                </div>
            </div>

            {/* Projects Grid */}
            {loading ? (
                <div className="flex justify-center py-20">
                    <div className="relative">
                        <div className="absolute inset-0 bg-accent/20 blur-xl rounded-full animate-pulse" />
                        <Loader2 className="w-10 h-10 text-accent animate-spin relative z-10" />
                    </div>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {projects.map((project, idx) => (
                        <GlassProjectCard key={project.id} project={project} index={idx} />
                    ))}
                </div>
            )}
        </div>
    );
}

const GlassProjectCard = ({ project, index }) => (
    <Link
        to={`/projects/${project.id}`}
        className="group relative block transition-all duration-500 hover:-translate-y-2"
        style={{ animationDelay: `${index * 100}ms` }}
    >
        {/* Card Container */}
        <div className="h-full bg-white/30 backdrop-blur-md border border-white/40 rounded-3xl p-6 shadow-lg hover:shadow-xl hover:shadow-accent/10 transition-shadow relative overflow-hidden">

            {/* Dynamic Background Gradient on Hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="absolute -right-10 -top-10 w-32 h-32 bg-accent/10 rounded-full blur-2xl group-hover:bg-accent/20 transition-colors duration-500" />

            {/* Content */}
            <div className="relative z-10 flex flex-col h-full">
                <div className="flex justify-between items-start mb-4">
                    <div className="px-3 py-1 rounded-full bg-white/40 border border-white/50 text-[10px] font-bold uppercase tracking-wider text-slate-600 shadow-sm">
                        {project.genre || 'Other'}
                    </div>
                    <div className="w-8 h-8 rounded-full bg-white/60 flex items-center justify-center text-accent shadow-sm group-hover:scale-110 transition-transform">
                        <BookOpen className="w-4 h-4" />
                    </div>
                </div>

                <h3 className="text-xl font-heading font-bold text-slate-800 mb-2 group-hover:text-accent transition-colors line-clamp-2">
                    {project.name}
                </h3>

                <div className="mt-auto space-y-3 pt-6">
                    <div className="flex items-center text-sm text-slate-500 font-body">
                        <Clock className="w-4 h-4 mr-2 opacity-70" />
                        {new Date(project.created_at || Date.now()).toLocaleDateString()}
                    </div>

                    <div className="w-full bg-white/30 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-accent h-full w-[40%] rounded-full opacity-60 group-hover:opacity-100 transition-opacity" />
                    </div>
                </div>
            </div>
        </div>
    </Link>
);
