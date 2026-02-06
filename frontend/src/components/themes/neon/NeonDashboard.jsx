import React from 'react';
import { Terminal, Database, Activity, Plus, Play, ChevronRight, Hash, Clock, Server } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function NeonDashboard({ projects, onCreateProject, loading, creating }) {
    // Cyberpunk/Terminal Aesthetic
    // Data-dense, monospace, high contrast

    const [localName, setLocalName] = React.useState('');
    const [localGenre, setLocalGenre] = React.useState('');
    // eslint-disable-next-line no-unused-vars
    const [isHovered, setIsHovered] = React.useState(null);

    const handleSubmit = (e) => {
        e.preventDefault();
        onCreateProject(localName, localGenre);
        setLocalName('');
        setLocalGenre('');
    };

    return (
        <div className="space-y-8 font-mono text-sm p-2">
            {/* Header Stats Block */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatBlock
                    label="SYSTEM_STATUS"
                    value="ONLINE"
                    color="text-secondary-accent"
                    icon={<Activity className="w-4 h-4 ml-2 animate-pulse" />}
                />
                <StatBlock
                    label="ACTIVE_NETWORKS"
                    value={projects.length.toString().padStart(2, '0')}
                    color="text-accent"
                    icon={<Database className="w-4 h-4 ml-2" />}
                />
                <StatBlock
                    label="MEMORY_ALLOC"
                    value="48%"
                    color="text-text"
                    icon={<Server className="w-4 h-4 ml-2" />}
                />
                <StatBlock
                    label="UPTIME"
                    value="14:02:11"
                    color="text-text-muted"
                    icon={<Clock className="w-4 h-4 ml-2" />}
                />
            </div>

            {/* Create Project Terminal */}
            <div className="border-l-2 border-accent bg-surface/50 backdrop-blur-sm p-6 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-2 opacity-20 group-hover:opacity-100 transition-opacity">
                    <Terminal className="w-24 h-24 text-accent transform rotate-12 translate-x-8 -translate-y-8" />
                </div>

                <h3 className="text-accent font-bold uppercase tracking-widest mb-6 flex items-center text-lg">
                    <span className="mr-2 text-secondary-accent">./</span>
                    INIT_NEW_PROJECT_SEQUENCE
                </h3>

                <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-6 items-end relative z-10">
                    <div className="flex-1 w-full space-y-2">
                        <label className="text-[10px] text-accent/70 uppercase tracking-widest">Target_ID (Name)</label>
                        <div className="flex items-center border-b border-accent/30 bg-bg/50 px-3 py-1 focus-within:border-accent transition-colors">
                            <span className="text-accent mr-3 font-bold">&gt;</span>
                            <input
                                className="bg-transparent border-none focus:outline-none w-full py-2 text-text placeholder:text-muted-foreground/30 font-mono text-base"
                                placeholder="ENTER_DESIGNATION..."
                                value={localName}
                                onChange={(e) => setLocalName(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="w-full md:w-72 space-y-2">
                        <label className="text-[10px] text-accent/70 uppercase tracking-widest">Protocol (Genre)</label>
                        <div className="flex items-center border-b border-accent/30 bg-bg/50 px-3 py-1 focus-within:border-accent transition-colors">
                            <Hash className="w-4 h-4 text-secondary-accent mr-3" />
                            <input
                                className="bg-transparent border-none focus:outline-none w-full py-2 text-text placeholder:text-muted-foreground/30 font-mono text-base"
                                list="genre-options"
                                placeholder="SELECT_PROTOCOL..."
                                value={localGenre}
                                onChange={(e) => setLocalGenre(e.target.value)}
                            />
                            <datalist id="genre-options">
                                <option value="wuxia">Wuxia_Protocol</option>
                                <option value="xianxia">Xianxia_Protocol</option>
                                <option value="litrpg">LitRPG_Protocol</option>
                                <option value="scifi">SciFi_Protocol</option>
                                <option value="fantasy">Fantasy_Protocol</option>
                                <option value="romance">Romance_Protocol</option>
                                <option value="system">System_Protocol</option>
                            </datalist>
                        </div>
                    </div>

                    <button
                        disabled={creating}
                        className="h-[46px] px-8 bg-accent/5 border border-accent text-accent hover:bg-accent hover:text-bg transition-all font-bold uppercase tracking-widest flex items-center justify-center min-w-[140px] shadow-[0_0_20px_rgba(0,243,255,0.1)] hover:shadow-[0_0_30px_rgba(0,243,255,0.4)]"
                    >
                        {creating ? <Activity className="w-5 h-5 animate-spin" /> : (
                            <>
                                EXECUTE <Play className="w-4 h-4 ml-2 fill-current" />
                            </>
                        )}
                    </button>
                </form>
            </div>

            {/* Project Grid */}
            <div className="mt-12">
                <div className="flex items-center justify-between mb-6 border-b border-border/50 pb-2">
                    <h3 className="font-bold flex items-center text-text-muted">
                        <Database className="w-4 h-4 mr-2 text-accent" />
                        MOUNTED_DATABASES
                    </h3>
                    <div className="text-xs text-secondary-accent animate-pulse">SCANNING_COMPLETED</div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-24 border border-dashed border-border/30 bg-surface/20">
                        <div className="flex flex-col items-center text-accent animate-pulse">
                            <Activity className="w-8 h-8 mb-4" />
                            <span className="tracking-widest">ACCESSING_SECTORS...</span>
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {projects.map((p) => (
                            <NeonProjectCard key={p.id} project={p} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

const NeonProjectCard = ({ project }) => {
    const navigate = useNavigate();

    return (
        <div
            onClick={() => navigate(`/projects/${project.id}`)}
            className="group relative border border-border bg-surface p-6 transition-all duration-300 hover:border-accent hover:shadow-[0_0_30px_rgba(0,243,255,0.15)] cursor-pointer overflow-hidden"
        >
            {/* Decorative Overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity" />

            {/* Top Bar */}
            <div className="flex justify-between items-start mb-6 relative z-10">
                <div className="flex-1">
                    <div className="text-[10px] text-accent mb-1 tracking-widest flex items-center">
                        <span className="w-2 h-2 rounded bg-secondary-accent mr-2 animate-pulse" />
                        ID: {project.id.toString().padStart(4, '0')}
                    </div>
                    <h4 className="font-bold text-xl text-text group-hover:text-accent transition-colors line-clamp-1">
                        {project.name}
                    </h4>
                </div>
                <div className={`px-2 py-1 text-[10px] border ${project.genre === 'xianxia' || project.genre === 'wuxia' ? 'border-purple-500/50 text-purple-400' : 'border-border text-text-muted'} uppercase tracking-wider backdrop-blur-md`}>
                    {project.genre}
                </div>
            </div>

            {/* Data Grid */}
            <div className="grid grid-cols-2 gap-4 text-xs font-mono relative z-10 border-t border-border/30 pt-4">
                <div>
                    <span className="block text-text-muted text-[10px] mb-1">CREATED</span>
                    <span className="text-text">{new Date(project.created_at || Date.now()).toLocaleDateString()}</span>
                </div>
                <div>
                    <span className="block text-text-muted text-[10px] mb-1">STATUS</span>
                    <span className="text-secondary-accent">ACTIVE</span>
                </div>
            </div>

            {/* Bottom Action */}
            <div className="mt-6 pt-4 border-t border-border/30 flex justify-between items-center relative z-10 opacity-70 group-hover:opacity-100 transition-opacity">
                <span className="text-[10px] text-text-muted">ACCESS_LEVEL_1</span>
                <span className="text-accent text-xs hover:underline flex items-center tracking-wider font-bold">
                    INIT_SESSION <ChevronRight className="w-3 h-3 ml-1" />
                </span>
            </div>

            {/* Corner Markers */}
            <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-accent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-accent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        </div>
    );
}

const StatBlock = ({ label, value, color = "text-text", icon }) => (
    <div className="border border-border bg-surface p-4 relative overflow-hidden group hover:border-accent/40 transition-colors">
        <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
            {icon}
        </div>
        <div className="text-[10px] text-text-muted uppercase mb-2 tracking-widest flex items-center">
            {label}
        </div>
        <div className={`text-2xl font-bold font-mono ${color} tracking-tighter`}>
            {value}
        </div>
        {/* Animated Loading Bar at bottom */}
        <div className="absolute bottom-0 left-0 h-[2px] bg-accent w-0 group-hover:w-full transition-all duration-700 ease-out" />
    </div>
);


