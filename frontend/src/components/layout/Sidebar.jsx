import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard } from 'lucide-react'
import { cn } from '@/lib/utils.js'
import { ThemeToggle } from '../theme-toggle'

const navItems = [
  { name: 'Проекты', href: '/', icon: LayoutDashboard },
]

export function Sidebar() {
  const location = useLocation()
  const pathname = location.pathname

  return (
    <div className="flex h-screen w-64 flex-col border-r border-border bg-muted/30">
      <div className="p-6">
        <h1 className="text-xl font-bold tracking-tight text-foreground">
          Ranobe Translator
        </h1>
      </div>
      <nav className="flex-1 space-y-1 px-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
          )
        })}
      </nav>
      <div className="border-t border-border p-4">
        <ThemeToggle />
        <div className="mt-4 text-xs text-muted-foreground text-center">
          &copy; 2024 LightNovel NLP
        </div>
      </div>
    </div>
  )
}
