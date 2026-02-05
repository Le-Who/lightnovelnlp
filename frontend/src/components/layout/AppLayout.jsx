import React from 'react'
import { Sidebar } from './Sidebar'

export function AppLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-white font-sans text-slate-950 antialiased">
      <Sidebar />
      <main className="flex-1 overflow-y-auto h-screen">
        <div className="container mx-auto py-8 px-8 max-w-7xl">
          {children}
        </div>
      </main>
    </div>
  )
}
