import React from 'react'

/**
 * NeonSkeleton — base shimmer bone for Neon Operator theme.
 * Renders an animated horizontal scan-shimmer in cyan tones.
 *
 * @param {string} className — additional Tailwind / inline class overrides
 */
export function NeonSkeleton({ className = '' }) {
  return (
    <div
      className={`relative overflow-hidden bg-surface/40 border border-accent/10 ${className}`}
      aria-hidden="true"
    >
      {/* Shimmer sweep */}
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.6s_infinite] bg-gradient-to-r from-transparent via-accent/10 to-transparent" />
    </div>
  )
}

/**
 * NeonProjectCardSkeleton — matches the layout of NeonProjectCard in DashboardPage.
 */
export function NeonProjectCardSkeleton() {
  return (
    <div className="relative border border-accent/10 bg-surface p-6 overflow-hidden">
      {/* ID tag */}
      <NeonSkeleton className="h-2.5 w-20 mb-3" />
      {/* Title */}
      <NeonSkeleton className="h-5 w-3/5 mb-6" />
      {/* Data grid */}
      <div className="grid grid-cols-2 gap-4 border-t border-accent/10 pt-4">
        <div>
          <NeonSkeleton className="h-2 w-16 mb-2" />
          <NeonSkeleton className="h-4 w-8" />
        </div>
        <div>
          <NeonSkeleton className="h-2 w-16 mb-2" />
          <NeonSkeleton className="h-4 w-12" />
        </div>
      </div>
      {/* Bottom action */}
      <div className="mt-6 pt-4 border-t border-accent/10 flex justify-between">
        <NeonSkeleton className="h-2 w-24" />
        <NeonSkeleton className="h-2 w-20" />
      </div>
    </div>
  )
}

/**
 * NeonFileRowSkeleton — matches a row in ChapterManager's file table.
 */
export function NeonFileRowSkeleton({ index = 0 }) {
  return (
    <div
      className="grid grid-cols-12 gap-4 p-3 items-center border-b border-accent/5"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* ID */}
      <div className="col-span-1">
        <NeonSkeleton className="h-2.5 w-8" />
      </div>
      {/* Filename */}
      <div className="col-span-4 flex items-center gap-2">
        <NeonSkeleton className="h-3 w-3 shrink-0" />
        <NeonSkeleton className="h-3 flex-1" />
      </div>
      {/* Size */}
      <div className="col-span-2">
        <NeonSkeleton className="h-2.5 w-14" />
      </div>
      {/* Status */}
      <div className="col-span-2">
        <NeonSkeleton className="h-4 w-16" />
      </div>
      {/* Actions */}
      <div className="col-span-3 flex justify-end gap-2">
        <NeonSkeleton className="h-6 w-6 rounded-sm" />
        <NeonSkeleton className="h-6 w-6 rounded-sm" />
        <NeonSkeleton className="h-6 w-6 rounded-sm" />
        <NeonSkeleton className="h-6 w-6 rounded-sm" />
      </div>
    </div>
  )
}
