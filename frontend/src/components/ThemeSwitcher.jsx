import React from 'react';
import { useTheme } from './theme-provider';

export function ThemeSwitcher() {
    const { theme, setTheme } = useTheme();

    const themes = [
        { id: 'paper-zen', name: 'Paper Zen' },
        { id: 'neon-operator', name: 'Neon Operator' },
        // { id: 'ink-blade', name: 'Ink & Blade' },
        // { id: 'aether-lens', name: 'Aether Lens' },
        // { id: 'brutalist-grid', name: 'Brutalist Grid' },
    ];

    return (
        <div className="fixed bottom-4 right-4 z-50 p-2 bg-surface border border-border rounded-lg shadow-lg opacity-90 hover:opacity-100 transition-opacity">
            <select
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="bg-bg text-text border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
            >
                {themes.map((t) => (
                    <option key={t.id} value={t.id}>
                        {t.name}
                    </option>
                ))}
            </select>
        </div>
    );
}
