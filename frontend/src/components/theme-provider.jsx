import { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext({
    theme: 'paper-zen',
    setTheme: () => null,
});

export function ThemeProvider({
    children,
    defaultTheme = 'paper-zen',
    storageKey = 'vite-ui-theme',
    ...props
}) {
    const [theme, setTheme] = useState(
        () => localStorage.getItem(storageKey) || defaultTheme
    );

    useEffect(() => {
        const root = window.document.documentElement;
        // Remove previous theme attributes if any (though we just set one)
        // Actually we just set the data-attribute
        root.setAttribute('data-theme', theme);
        localStorage.setItem(storageKey, theme);
    }, [theme, storageKey]);

    return (
        <ThemeContext.Provider {...props} value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

export const useTheme = () => {
    const context = useContext(ThemeContext);

    if (context === undefined)
        throw new Error('useTheme must be used within a ThemeProvider');

    return context;
};
