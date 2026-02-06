import React from 'react';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { Activity, Terminal, Database, Cpu } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

export const NeonOperatorLayout = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const nav = (path) => {
        navigate(path);
    };

    const isActive = (path) => location.pathname === path || (path !== '/' && location.pathname.startsWith(path));

    return (
        <div className="min-h-screen bg-bg text-text font-mono flex overflow-hidden">
            {/* Left Sidebar - System Status */}
            <aside className="w-16 md:w-64 border-r border-accent/20 bg-surface/50 flex flex-col shrink-0">
                <div className="h-14 border-b border-accent/20 flex items-center justify-center md:justify-start md:px-4 cursor-pointer" onClick={() => nav('/')}>
                    <Cpu className="h-6 w-6 text-accent animate-pulse" />
                    <span className="ml-2 font-bold text-accent hidden md:inline tracking-widest">SYS.OP</span>
                </div>
                <nav className="flex-1 py-4 flex flex-col gap-2">
                    <div
                        onClick={() => nav('/')}
                        className={`px-2 md:px-4 py-2 cursor-pointer flex items-center text-sm md:text-base border-l-2 transition-all ${isActive('/') ? 'bg-accent/10 border-accent text-accent' : 'border-transparent hover:border-accent/50 text-muted-foreground'}`}
                    >
                        <Terminal className="h-4 w-4 mr-3" />
                        <span className="hidden md:inline">Dashboard</span>
                    </div>
                    <div className="px-2 md:px-4 py-2 flex items-center text-sm md:text-base border-l-2 border-transparent text-muted-foreground opacity-50 cursor-not-allowed">
                        <Database className="h-4 w-4 mr-3" />
                        <span className="hidden md:inline">Projects</span>
                    </div>
                </nav>
                <div className="p-4 border-t border-accent/20 text-xs text-muted-foreground hidden md:block">
                    <div><span className="text-accent">MEM:</span> 24%</div>
                    <div><span className="text-accent">NET:</span> ONLINE</div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Top Status Bar */}
                <header className="h-14 border-b border-accent/20 bg-bg flex items-center justify-between px-6">
                    <div className="text-xs uppercase tracking-widest text-muted-foreground flex items-center">
                        <span className="w-2 h-2 rounded-full bg-accent mr-2 animate-ping" />
                        System Online // v2.0.4
                    </div>
                    <div className="flex items-center gap-4">
                        <Activity className="h-4 w-4 text-accent" />
                        <span className="text-xs">LATENCY: 12ms</span>
                    </div>
                </header>

                <main className="flex-1 overflow-auto p-4 md:p-6 custom-scrollbar">
                    <div className="border border-accent/10 p-1 min-h-full relative">
                        {/* Corner decorations */}
                        <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-accent"></div>
                        <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-accent"></div>
                        <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-accent"></div>
                        <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-accent"></div>

                        <div className="relative z-10 p-4">
                            {children}
                        </div>
                    </div>
                </main>
            </div>

            <div className="fixed bottom-6 right-6 z-50">
                <ThemeSwitcher />
            </div>
        </div>
    );
};
