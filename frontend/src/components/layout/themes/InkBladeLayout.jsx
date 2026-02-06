import React from 'react';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { ScrollText, PenTool } from 'lucide-react';

export const InkBladeLayout = ({ children }) => {
    return (
        <div className="min-h-screen bg-bg text-text custom-cursor-brush">
            <div className="flex flex-col md:flex-row min-h-screen">
                {/* Navigation - Vertical Banner Style */}
                <nav className="w-full md:w-24 bg-surface border-r border-border flex md:flex-col items-center py-6 gap-8 shadow-xl z-20 sticky top-0 md:h-screen">
                    <div className="w-12 h-12 rounded-full border-2 border-accent flex items-center justify-center bg-bg shadow-md">
                        <span className="font-heading text-xl text-accent">L</span>
                    </div>

                    <div className="flex-1 flex md:flex-col gap-6 items-center justify-center">
                        <div className="writing-vertical-rl text-lg font-heading tracking-widest text-text hover:text-accent transition-colors cursor-pointer py-4 border-l-2 border-transparent hover:border-accent">
                            DASHBOARD
                        </div>
                        <div className="writing-vertical-rl text-lg font-heading tracking-widest text-muted-foreground hover:text-accent transition-colors cursor-pointer py-4 border-l-2 border-transparent hover:border-accent">
                            LIBRARY
                        </div>
                    </div>

                    <div className="text-secondary opacity-50">
                        <PenTool className="w-6 h-6" />
                    </div>
                </nav>

                {/* Main Content - Scroll */}
                <main className="flex-1 p-8 md:p-16 overflow-y-auto bg-gradient-to-b from-bg to-surface/30">
                    <div className="max-w-5xl mx-auto">
                        {/* Header Seal */}
                        <div className="flex justify-end mb-12 opacity-80">
                            <div className="border-4 border-accent p-2 rounded-sm rotate-3">
                                <div className="border border-accent p-2 font-heading font-bold text-accent text-xs tracking-widest uppercase">
                                    OFFICIAL
                                </div>
                            </div>
                        </div>

                        {children}
                    </div>
                </main>
            </div>

            <div className="fixed bottom-6 right-6 z-50">
                <ThemeSwitcher />
            </div>
        </div>
    );
};
