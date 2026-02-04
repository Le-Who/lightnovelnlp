import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard } from 'lucide-react'
import { cn } from '../../lib/utils'

const navItems = [
  { name: 'Проекты', href: '/', icon: LayoutDashboard },
]

export function Sidebar() {
  const location = useLocation()
  const pathname = location.pathname

  return (
    <div className="flex h-screen w-64 flex-col border-r bg-slate-50/50">
      <div className="p-6">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">
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
                  ? "bg-slate-900 text-slate-50"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
          )
        })}
      </nav>
      <div className="border-t p-4 text-xs text-slate-500 text-center">
        &copy; 2024 LightNovel NLP
      </div>
    </div>
  )
}
