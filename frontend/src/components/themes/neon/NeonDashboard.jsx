import React from 'react';

import { Terminal, Database, Cpu, Activity, Plus, Play, ChevronRight } from 'lucide-react';

export function NeonDashboard({ projects, onCreateProject, loading, creating }) {
    // Cyberpunk/Terminal Aesthetic
    // Data-dense, monospace, high contrast

    const [localName, setLocalName] = React.useState('');
    const [localGenre, setLocalGenre] = React.useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        onCreateProject(localName, localGenre);
        setLocalName('');
        setLocalGenre('');
    };

    return (
        <div className="space-y-6 font-mono text-sm">
            {/* Header Stats Block */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <StatBlock label="SYSTEM_STATUS" value="ONLINE" color="text-accent" />
                <StatBlock label="ACTIVE_PROJECTS" value={projects.length.toString().padStart(2, '0')} />
                <StatBlock label="MEMORY_ALLOC" value="48%" />
                <StatBlock label="UPTIME" value="14:02:11" />
            </div>

            {/* Create Project Terminal */}
            <div className="border border-accent/30 bg-surface/80 p-1 relative group">
                {/* Decorative corners */}
                <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-accent opacity-50 group-hover:opacity-100 transition-opacity" />
                <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-accent opacity-50 group-hover:opacity-100 transition-opacity" />
                <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-accent opacity-50 group-hover:opacity-100 transition-opacity" />
                <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-accent opacity-50 group-hover:opacity-100 transition-opacity" />

                <div className="p-4">
                    <h3 className="text-accent font-bold uppercase tracking-wider mb-4 flex items-center">
                        <Terminal className="w-4 h-4 mr-2" />
                        INIT_NEW_PROJECT_SEQUENCE
                    </h3>
                    <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4 items-end">
                        <div className="flex-1 w-full relative">
                            <label className="text-xs text-muted-foreground block mb-1">PROJECT_ID (NAME)</label>
                            <div className="flex items-center border border-border bg-bg px-2">
                                <span className="text-accent mr-2">&gt;</span>
                                <input
                                    className="bg-transparent border-none focus:outline-none w-full py-2 text-text placeholder:text-muted-foreground/30"
                                    placeholder="ENTER_NAME..."
                                    value={localName}
                                    onChange={(e) => setLocalName(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="w-full md:w-64">
                            <label className="text-xs text-muted-foreground block mb-1">GENRE_CLASS</label>
                            <div className="flex items-center border border-border bg-bg px-2">
                                <span className="text-accent mr-2">&gt;</span>
                                <select
                                    className="bg-transparent border-none focus:outline-none w-full py-2 text-text appearance-none"
                                    value={localGenre}
                                    onChange={(e) => setLocalGenre(e.target.value)}
                                >
                                    <option value="" className="bg-bg">SELECT_CLASS...</option>
                                    <option value="wuxia" className="bg-bg">WUXIA</option>
                                    <option value="xianxia" className="bg-bg">XIANXIA</option>
                                    <option value="litrpg" className="bg-bg">LITRPG</option>
                                    <option value="scifi" className="bg-bg">SCI-FI</option>
                                    <option value="fantasy" className="bg-bg">FANTASY</option>
                                </select>
                            </div>
                        </div>
                        <button
                            disabled={creating}
                            className="bg-accent/10 border border-accent text-accent hover:bg-accent hover:text-bg px-6 py-2 transition-all font-bold uppercase tracking-widest flex items-center h-[42px]"
                        >
                            {creating ? <Activity className="w-4 h-4 animate-spin" /> : 'EXECUTE'}
                        </button>
                    </form>
                </div>
            </div>

            {/* Project Grid */}
            <div className="mt-8">
                <div className="flex items-center justify-between mb-4 border-b border-border pb-2">
                    <h3 className="font-bold flex items-center">
                        <Database className="w-4 h-4 mr-2 text-accent" />
                        MOUNTED_DATABASES
                    </h3>
                    <div className="text-xs text-muted-foreground">SCANNING_COMPLETED</div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-12 text-accent animate-pulse">
                        <Activity className="w-6 h-6 mr-2" /> READING_SECTORS...
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {projects.map((p) => (
                            <NeonProjectCard key={p.id} project={p} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

const NeonProjectCard = ({ project }) => (
    <div className="border border-border p-4 hover:border-accent hover:shadow-[0_0_15px_rgba(0,255,148,0.15)] transition-all cursor-pointer group relative overflow-hidden bg-surface/50">
        {/* Scanline overlay */}
        <div className="absolute inset-0 bg-scanline pointer-events-none opacity-0 group-hover:opacity-10" />

        <div className="flex justify-between items-start mb-2">
            <h4 className="font-bold text-lg group-hover:text-accent transition-colors">
                {project.name.toUpperCase()}
            </h4>
            <div className={`px-1 text-[10px] border ${project.genre === 'xianxia' ? 'border-purple-500 text-purple-400' : 'border-border text-muted-foreground'} uppercase`}>
                {project.genre}
            </div>
        </div>

        <div className="space-y-1 text-xs text-muted-foreground mt-4 font-mono">
            <div className="flex justify-between">
                <span>ID:</span>
                <span>{project.id.substring(0, 8)}...</span>
            </div>
            <div className="flex justify-between">
                <span>CREATED:</span>
                <span>{new Date(project.created_at || Date.now()).toLocaleDateString()}</span>
            </div>
            <div className="flex justify-between">
                <span>CHAPTERS:</span>
                <span className="text-white">--</span>
            </div>
        </div>

        <div className="mt-4 pt-2 border-t border-border flex justify-end">
            <a href={`/projects/${project.id}`} className="text-accent text-xs hover:underline flex items-center">
                ACCESS_DATA <ChevronRight className="w-3 h-3 ml-1" />
            </a>
        </div>
    </div>
);

const StatBlock = ({ label, value, color = "text-white" }) => (
    <div className="border border-border p-2 bg-bg relative">
        <div className="text-[10px] text-muted-foreground uppercase mb-1">{label}</div>
        <div className={`text-xl font-bold font-mono ${color}`}>{value}</div>
        {/* Corner accent */}
        <div className="absolute top-0 right-0 w-2 h-2 bg-border/50" />
    </div>
);


