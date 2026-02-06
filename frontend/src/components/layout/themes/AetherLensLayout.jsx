import React from 'react';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { Home, Compass, Layers, Zap } from 'lucide-react';

export const AetherLensLayout = ({ children }) => {
    return (
        <div className="min-h-screen bg-bg text-text font-sans overflow-hidden relative selection:bg-accent/30 selection:text-accent-foreground">
            {/* Animated Background Orbs */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-accent/20 blur-[120px] animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-pink-400/20 blur-[150px] animate-pulse delay-1000" />
            </div>

            {/* Glass Container */}
            <main className="relative z-10 container mx-auto h-screen flex flex-col p-4 md:p-8">
                <div className="flex-1 backdrop-blur-md bg-surface/40 rounded-3xl border border-white/20 shadow-2xl overflow-hidden flex flex-col">
                    {/* Top Bar */}
                    <header className="h-16 border-b border-white/10 flex items-center justify-between px-8">
                        <h1 className="text-xl font-heading font-light tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-text to-accent">
                            AETHER LENS
                        </h1>
                        <div className="flex gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-400/80 shadow-sm" />
                            <div className="w-3 h-3 rounded-full bg-yellow-400/80 shadow-sm" />
                            <div className="w-3 h-3 rounded-full bg-green-400/80 shadow-sm" />
                        </div>
                    </header>

                    {/* Content */}
                    <div className="flex-1 overflow-auto p-8 custom-scrollbar-glass">
                        {children}
                    </div>
                </div>

                {/* Floating Dock Navigation */}
                <nav className="mt-6 mx-auto bg-surface/80 backdrop-blur-xl border border-white/30 rounded-full px-6 py-3 flex items-center gap-6 shadow-xl transform hover:scale-105 transition-transform duration-300">
                    <NavItem icon={<Home size={20} />} active />
                    <NavItem icon={<Compass size={20} />} />
                    <NavItem icon={<Layers size={20} />} />
                    <div className="w-px h-6 bg-border mx-2" />
                    <NavItem icon={<Zap size={20} />} />
                </nav>
            </main>

            <div className="fixed bottom-6 right-6 z-50">
                <ThemeSwitcher />
            </div>
        </div>
    );
};

const NavItem = ({ icon, active }) => (
    <div className={`p-2 rounded-xl transition-all cursor-pointer hover:bg-white/20 hover:-translate-y-1 ${active ? 'bg-white/30 text-accent shadow-inner' : 'text-muted-foreground'}`}>
        {icon}
    </div>
);
