import React from 'react';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

export const PaperZenLayout = ({ children }) => {
    return (
        <div className="min-h-screen bg-bg text-text font-serif transition-colors duration-500">
            <header className="sticky top-0 z-40 w-full backdrop-blur-sm border-b border-border/40 bg-bg/80">
                <div className="container flex h-16 items-center justify-center max-w-4xl mx-auto px-4 relative">
                    <h1 className="text-xl font-heading font-medium tracking-wide">LIGHT NOVEL TRANSLATOR</h1>
                    <div className="absolute right-4 text-sm text-muted-foreground opacity-50 hover:opacity-100 transition-opacity">
                        Volume 1
                    </div>
                </div>
            </header>
            <main className="container max-w-3xl mx-auto py-12 px-6 md:px-12 bg-surface shadow-sm min-h-[calc(100vh-4rem)] my-8 rounded-sm paper-texture">
                {children}
            </main>
            <div className="fixed bottom-6 right-6 z-50">
                <ThemeSwitcher />
            </div>
        </div>
    );
};
