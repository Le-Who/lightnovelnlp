import React, { useMemo } from 'react';
import { useTheme } from '../theme-provider';
import { Sidebar } from './Sidebar'; // Fallback

// Theme Layouts
import { PaperZenLayout } from './themes/PaperZenLayout';
import { NeonOperatorLayout } from './themes/NeonOperatorLayout';
import { InkBladeLayout } from './themes/InkBladeLayout';
import { AetherLensLayout } from './themes/AetherLensLayout';
import { BrutalistGridLayout } from './themes/BrutalistGridLayout';

export function AppLayout({ children }) {
  const { theme } = useTheme();

  const LayoutComponent = useMemo(() => {
    switch (theme) {
      case 'paper-zen':
        return PaperZenLayout;
      case 'neon-operator':
        return NeonOperatorLayout;
      case 'ink-blade':
        return InkBladeLayout;
      case 'aether-lens':
        return AetherLensLayout;
      case 'brutalist-grid':
        return BrutalistGridLayout;
      default:
        return PaperZenLayout;
    }
  }, [theme]);

  return (
    <LayoutComponent>
      {children}
    </LayoutComponent>
  );
}
