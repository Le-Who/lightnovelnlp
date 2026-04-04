import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'
import { Activity, XCircle, Play, RefreshCw, Cpu, AlertOctagon, CheckCircle2, Clock, Zap } from 'lucide-react'

// ─── Neon Status Config ───────────────────────────────────────────
const STATUS_CONFIG = {
  completed: {
    glyph: '✓',
    label: 'COMPLETED',
    color: 'text-secondary-accent',
    border: 'border-secondary-accent/30',
    glow: 'shadow-[0_0_12px_rgba(10,255,104,0.25)]',
    bar: 'bg-secondary-accent',
    barGlow: 'shadow-[0_0_8px_rgba(10,255,104,0.6)]',
  },
  running: {
    glyph: '⟳',
    label: 'PROCESSING',
    color: 'text-accent',
    border: 'border-accent/40',
    glow: 'shadow-[0_0_15px_rgba(0,243,255,0.2)]',
    bar: 'bg-accent',
    barGlow: 'shadow-[0_0_8px_rgba(0,243,255,0.6)]',
  },
  pending: {
    glyph: '◈',
    label: 'QUEUED',
    color: 'text-text-muted',
    border: 'border-border/40',
    glow: '',
    bar: 'bg-text-muted/50',
    barGlow: '',
  },
  failed: {
    glyph: '✕',
    label: 'FAILED',
    color: 'text-destructive',
    border: 'border-destructive/30',
    glow: 'shadow-[0_0_12px_rgba(255,42,109,0.2)]',
    bar: 'bg-destructive',
    barGlow: 'shadow-[0_0_8px_rgba(255,42,109,0.5)]',
  },
  cancelled: {
    glyph: '⊘',
    label: 'ABORTED',
    color: 'text-text-muted',
    border: 'border-border/20',
    glow: '',
    bar: 'bg-text-muted/30',
    barGlow: '',
  },
}

const getConfig = (status) => STATUS_CONFIG[status] ?? STATUS_CONFIG.pending

const JOB_TYPE_LABEL = {
  analyze: 'BATCH_ANALYSIS',
  translate: 'BATCH_TRANSLATE',
}

// ─── Helper: format datetime ──────────────────────────────────────
function fmtTime(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function fmtDuration(start, end) {
  if (!start) return null
  const ms = (end ? new Date(end) : new Date()) - new Date(start)
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s}s`
  return `${Math.floor(s / 60)}m ${s % 60}s`
}

// ─── Sub-components ───────────────────────────────────────────────
function NeonDispatchButton({ onClick, disabled, loading, icon: Icon, label, accentColor = 'accent' }) {
  const colorMap = {
    accent: {
      base: 'border-accent text-accent',
      hover: 'hover:bg-accent hover:text-bg hover:shadow-[0_0_25px_rgba(0,243,255,0.4)]',
      active: 'bg-accent/5',
      spinColor: 'text-accent',
    },
    green: {
      base: 'border-secondary-accent text-secondary-accent',
      hover: 'hover:bg-secondary-accent hover:text-bg hover:shadow-[0_0_25px_rgba(10,255,104,0.4)]',
      active: 'bg-secondary-accent/5',
      spinColor: 'text-secondary-accent',
    },
  }
  const c = colorMap[accentColor] ?? colorMap.accent

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        flex items-center gap-2 px-6 py-2.5 border font-bold uppercase tracking-widest text-[11px]
        transition-all duration-200 ${c.base} ${c.active} ${disabled ? 'opacity-40 cursor-not-allowed' : c.hover}
      `}
    >
      {loading
        ? <Activity className="w-3.5 h-3.5 animate-spin" />
        : <Icon className="w-3.5 h-3.5" />
      }
      {label}
    </button>
  )
}

function NeonProgressBar({ pct, status }) {
  const cfg = getConfig(status)
  const isActive = status === 'running'

  return (
    <div className="relative w-full h-[6px] bg-surface/80 border border-accent/10 overflow-hidden">
      <div
        className={`h-full transition-all duration-700 ease-out ${cfg.bar} ${cfg.barGlow}`}
        style={{ width: `${pct}%` }}
      />
      {/* scanline for running jobs */}
      {isActive && (
        <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_0%,rgba(0,243,255,0.25)_50%,transparent_100%)] animate-scan pointer-events-none" />
      )}
    </div>
  )
}

function NeonJobCard({ job, onCancel }) {
  const cfg = getConfig(job.status)
  const isActive = job.status === 'pending' || job.status === 'running'
  const duration = fmtDuration(job.started_at, job.completed_at)

  return (
    <div className={`border ${cfg.border} ${cfg.glow} bg-surface/40 relative overflow-hidden transition-all duration-300 group`}>
      {/* Animated corner markers for running jobs */}
      {isActive && (
        <>
          <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-accent animate-pulse" />
          <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-accent animate-pulse" />
        </>
      )}

      {/* Top row */}
      <div className="flex items-start justify-between p-4 border-b border-accent/10">
        <div className="flex items-center gap-3">
          {/* Status glyph */}
          <span className={`font-mono font-bold text-sm ${cfg.color} ${isActive ? 'animate-pulse' : ''}`}>
            {cfg.glyph}
          </span>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-text text-xs tracking-widest uppercase">
                {JOB_TYPE_LABEL[job.job_type] ?? job.job_type}
              </span>
              <span className={`px-1.5 py-0.5 text-[9px] font-bold border tracking-widest uppercase ${cfg.border} ${cfg.color}`}>
                {cfg.label}
              </span>
            </div>
            <div className="text-[10px] text-text-muted mt-0.5 font-mono">
              JOB_ID: {String(job.id).padStart(4, '0')}
            </div>
          </div>
        </div>

        {/* Action / timer */}
        <div className="flex flex-col items-end gap-1.5">
          {isActive && onCancel && (
            <button
              onClick={() => onCancel(job.id)}
              className="flex items-center gap-1.5 px-3 py-1 border border-destructive/40 text-destructive hover:bg-destructive/10 text-[10px] font-bold uppercase tracking-wider transition-colors"
            >
              <XCircle className="w-3 h-3" />
              ABORT
            </button>
          )}
          {duration && (
            <span className="text-[10px] text-text-muted font-mono flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {duration}
            </span>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="p-4 space-y-3">
        {/* Progress */}
        <div>
          <div className="flex justify-between items-center mb-1.5">
            <span className="text-[10px] text-text-muted uppercase tracking-widest">
              Progress
            </span>
            <span className={`font-mono font-bold text-sm ${cfg.color}`}>
              {job.progress_percentage}%
              <span className="text-[10px] text-text-muted font-normal ml-2">
                ({job.processed_items}/{job.total_items})
              </span>
            </span>
          </div>
          <NeonProgressBar pct={job.progress_percentage} status={job.status} />
        </div>

        {/* Failed items notice */}
        {job.failed_items > 0 && (
          <div className="flex items-center gap-2 text-destructive text-[10px] font-bold uppercase">
            <AlertOctagon className="w-3 h-3" />
            {job.failed_items} ITEM(S) FAILED
          </div>
        )}

        {/* Timestamps */}
        <div className="grid grid-cols-3 gap-2 text-[10px] font-mono border-t border-accent/10 pt-3">
          <div>
            <div className="text-text-muted mb-0.5">CREATED</div>
            <div className="text-text">{fmtTime(job.created_at)}</div>
          </div>
          <div>
            <div className="text-text-muted mb-0.5">STARTED</div>
            <div className="text-text">{fmtTime(job.started_at)}</div>
          </div>
          <div>
            <div className="text-text-muted mb-0.5">FINISHED</div>
            <div className="text-text">{fmtTime(job.completed_at)}</div>
          </div>
        </div>

        {/* Error */}
        {job.error_message && (
          <div className="border border-destructive/30 bg-destructive/5 p-2.5 text-[10px] font-mono text-destructive">
            <div className="font-bold mb-1 uppercase tracking-widest">ERROR_LOG:</div>
            {job.error_message}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────
export default function BatchProcessor({ projectId }) {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [creatingJob, setCreatingJob] = useState(false)
  const [activeJobs, setActiveJobs] = useState(new Set())

  const loadJobs = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/batch/${projectId}/jobs`)
      const data = Array.isArray(res.data) ? res.data : []
      setJobs(data)

      const active = new Set()
      data.forEach(job => {
        if (job.status === 'pending' || job.status === 'running') active.add(job.id)
      })
      setActiveJobs(active)
    } catch (e) {
      console.error('Error loading jobs:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) loadJobs()
  }, [projectId])

  // Real-time polling for active jobs
  useEffect(() => {
    if (activeJobs.size === 0) return
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/batch/${projectId}/jobs`)
        const data = Array.isArray(res.data) ? res.data : []
        setJobs(data)
        const stillActive = new Set()
        data.forEach(job => {
          if (job.status === 'pending' || job.status === 'running') stillActive.add(job.id)
        })
        setActiveJobs(stillActive)
        if (stillActive.size === 0) clearInterval(interval)
      } catch (e) {
        console.error('Error updating jobs:', e)
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [activeJobs, projectId])

  const createAnalyzeJob = async () => {
    setCreatingJob(true)
    try {
      await api.post(`/batch/${projectId}/analyze-chapters`, {})
      loadJobs()
    } catch (e) {
      console.error('Error creating analyze job:', e)
    } finally {
      setCreatingJob(false)
    }
  }

  const createTranslateJob = async () => {
    setCreatingJob(true)
    try {
      await api.post(`/batch/${projectId}/translate-chapters`, {})
      loadJobs()
    } catch (e) {
      console.error('Error creating translate job:', e)
    } finally {
      setCreatingJob(false)
    }
  }

  const cancelJob = async (jobId) => {
    if (!confirm(`ABORT JOB_ID: ${String(jobId).padStart(4, '0')}? ACTION IS IRREVERSIBLE.`)) return
    try {
      await api.delete(`/batch/jobs/${jobId}`)
      loadJobs()
    } catch (e) {
      console.error('Error cancelling job:', e)
    }
  }

  return (
    <div className="space-y-8 font-mono text-sm">
      {/* Dispatch Panel */}
      <div className="border-l-2 border-accent bg-surface/50 backdrop-blur-sm p-6 relative overflow-hidden group">
        {/* Decorative CPU */}
        <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
          <Cpu className="w-24 h-24 text-accent transform -rotate-12 translate-x-6 -translate-y-6" />
        </div>

        <h3 className="text-accent font-bold uppercase tracking-widest mb-2 flex items-center text-base">
          <span className="mr-2 text-secondary-accent">./</span>
          BATCH_DISPATCH_CONSOLE
        </h3>
        <p className="text-[10px] text-text-muted mb-6 uppercase tracking-wider">
          Queue multi-chapter operations. Progress is tracked in real time.
        </p>

        <div className="flex flex-wrap gap-4">
          <NeonDispatchButton
            onClick={createAnalyzeJob}
            disabled={creatingJob}
            loading={creatingJob}
            icon={Play}
            label="ANALYZE ALL CHAPTERS"
            accentColor="green"
          />
          <NeonDispatchButton
            onClick={createTranslateJob}
            disabled={creatingJob}
            loading={creatingJob}
            icon={RefreshCw}
            label="TRANSLATE ALL CHAPTERS"
            accentColor="accent"
          />
        </div>

        <div className="mt-5 grid grid-cols-2 gap-4 text-[10px] text-text-muted border-t border-accent/10 pt-4">
          <div className="flex items-start gap-2">
            <Zap className="w-3 h-3 text-secondary-accent mt-0.5 shrink-0" />
            <span><span className="text-secondary-accent font-bold">ANALYZE:</span> Term extraction, relationship mapping, chapter summaries</span>
          </div>
          <div className="flex items-start gap-2">
            <Zap className="w-3 h-3 text-accent mt-0.5 shrink-0" />
            <span><span className="text-accent font-bold">TRANSLATE:</span> Glossary-aware translation of all untranslated chapters</span>
          </div>
        </div>
      </div>

      {/* Job History */}
      <div>
        <div className="flex items-center justify-between mb-4 border-b border-accent/20 pb-2">
          <h3 className="text-base font-bold text-text-muted flex items-center gap-2 uppercase tracking-widest">
            <Activity className="w-4 h-4 text-accent" />
            JOB_HISTORY
          </h3>
          {activeJobs.size > 0 && (
            <div className="text-[10px] text-secondary-accent animate-pulse uppercase tracking-widest flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary-accent" />
              {activeJobs.size} ACTIVE
            </div>
          )}
        </div>

        {loading && jobs.length === 0 ? (
          /* Loading skeletons */
          <div className="space-y-4">
            {[0, 1].map(i => (
              <div key={i} className="border border-accent/10 bg-surface/40 animate-pulse">
                <div className="p-4 border-b border-accent/10 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-4 h-4 bg-accent/10 rounded-sm" />
                    <div className="space-y-1.5">
                      <div className="h-3 w-32 bg-accent/10 rounded-sm" />
                      <div className="h-2 w-20 bg-accent/5 rounded-sm" />
                    </div>
                  </div>
                </div>
                <div className="p-4 space-y-3">
                  <div className="h-[6px] bg-accent/10 rounded-sm" />
                  <div className="grid grid-cols-3 gap-2">
                    <div className="h-6 bg-accent/5 rounded-sm" />
                    <div className="h-6 bg-accent/5 rounded-sm" />
                    <div className="h-6 bg-accent/5 rounded-sm" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : jobs.length === 0 ? (
          /* Empty state */
          <div className="border border-dashed border-accent/20 bg-surface/10 py-16 flex flex-col items-center justify-center text-center">
            <div className="text-accent/20 font-mono text-4xl mb-4 tracking-tighter select-none">
              [ 0x00 ]
            </div>
            <div className="text-[10px] text-text-muted uppercase tracking-widest">
              NO_JOBS_FOUND. DISPATCH A BATCH OPERATION ABOVE.
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.map(job => (
              <NeonJobCard
                key={job.id}
                job={job}
                onCancel={cancelJob}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
