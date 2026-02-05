import React from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils.js'

function Spinner({ className, ...props }) {
  return (
    <Loader2
      className={cn("h-4 w-4 animate-spin", className)}
      role="status"
      aria-label="Loading"
      {...props}
    />
  )
}

export { Spinner }
