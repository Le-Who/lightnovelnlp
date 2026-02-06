import React from 'react';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

export const BrutalistGridLayout = ({ children }) => {
    return (
        <div className="min-h-screen bg-bg text-text font-mono border-4 border-black">
            <div className="grid grid-cols-1 md:grid-cols-[250px_1fr] min-h-[calc(100vh-8px)] divide-y-4 md:divide-y-0 md:divide-x-4 divide-black">
                {/* Sidebar */}
                <aside className="bg-surface p-0 flex flex-col">
                    <div className="p-4 border-b-4 border-black bg-accent text-white font-black text-2xl uppercase tracking-tighter">
                        NLP_TRANSLATOR
                    </div>
                    <nav className="flex-1 flex flex-col divide-y-2 divide-black">
                        <NavItem label="1. DASHBOARD" active />
                        <NavItem label="2. PROJECTS" />
                        <NavItem label="3. SETTINGS" />
                        <div className="flex-1 bg-stripes-pattern"></div>
                    </nav>
                    <div className="p-4 border-t-4 border-black font-bold text-xs uppercase">
                        STATUS: ACTIVE
                    </div>
                </aside>

                {/* Main Content */}
                <main className="divide-y-4 divide-black flex flex-col">
                    <header className="h-16 flex items-center px-6 bg-bg justify-between">
                        <h2 className="font-heading text-xl font-black uppercase">Main_View_01</h2>
                        <div className="bg-black text-white px-2 py-1 text-xs font-bold font-mono">
                            SYS_READY
                        </div>
                    </header>

                    <div className="flex-1 p-0 overflow-auto bg-bg">
                        {/* In Brutalist, we remove padding sometimes, or make it intentional */}
                        <div className="p-8">
                            {children}
                        </div>
                    </div>
                </main>
            </div>

            <div className="fixed bottom-6 right-6 z-50 border-2 border-black bg-white shadow-[4px_4px_0px_#000]">
                <ThemeSwitcher />
            </div>
        </div>
    );
};

const NavItem = ({ label, active }) => (
    <div className={`p-4 font-bold uppercase cursor-pointer hover:bg-black hover:text-white transition-none ${active ? 'bg-black text-white' : 'bg-bg text-text'}`}>
        {label}
    </div>
);
