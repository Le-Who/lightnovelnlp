import { useState, useEffect } from 'react';
import { useTheme } from '../components/theme-provider';
import React from 'react';

// Default Views
// We will lazy load theme specific views to avoid bundle bloat (optional, but good practice)
// For now, straightforward imports to keep it simple and robust

// Neon Views
import { NeonDashboard } from '../components/themes/neon/NeonDashboard';
import { NeonProjectPage } from '../components/themes/neon/NeonProjectPage';
// import { AetherDashboard } from '../components/themes/aether/AetherDashboard';
// import { AetherProjectPage } from '../components/themes/aether/AetherProjectPage';

// Mapping
const themeViews = {
    'neon-operator': {
        Dashboard: NeonDashboard,
        ProjectPage: NeonProjectPage,
    },
    /* 
    'aether-lens': {
        Dashboard: AetherDashboard,
        ProjectPage: AetherProjectPage,
    }, 
    */
    // Future themes...
    'default': {
        Dashboard: null, // Null means "Use Default Impl"
        ProjectPage: null,
    }
};

export function useThemeView() {
    const { theme } = useTheme();
    const [views, setViews] = useState(themeViews['default']);

    useEffect(() => {
        const currentThemeViews = themeViews[theme] || themeViews['default'];
        setViews(currentThemeViews);
    }, [theme]);

    return views;
}
