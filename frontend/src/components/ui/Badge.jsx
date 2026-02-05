import React from 'react'
import { cn } from '@/lib/utils.js'

const variants = {
  default: 'border-transparent bg-slate-900 text-slate-50 hover:bg-slate-900/80',
  secondary: 'border-transparent bg-slate-100 text-slate-900 hover:bg-slate-100/80',
  destructive: 'border-transparent bg-red-500 text-slate-50 hover:bg-red-500/80',
  outline: 'text-slate-950',
  success: 'border-transparent bg-green-500 text-white hover:bg-green-500/80',
  warning: 'border-transparent bg-yellow-500 text-white hover:bg-yellow-500/80',
  info: 'border-transparent bg-blue-500 text-white hover:bg-blue-500/80',
}

function Badge({ className, variant = 'default', ...props }) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-950 focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
