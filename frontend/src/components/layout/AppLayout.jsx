import React from 'react'
import { Sidebar } from './Sidebar'

export function AppLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-background font-sans text-foreground antialiased">
      <Sidebar />
      <main className="flex-1 overflow-y-auto h-screen">
        <div className="container mx-auto py-8 px-8 max-w-7xl">
          {children}
        </div>
      </main>
    </div>
  )
}
