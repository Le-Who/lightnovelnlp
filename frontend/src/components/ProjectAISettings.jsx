import React, { useState, useEffect, useCallback } from 'react'
import { Settings, Zap, Globe, Brain, Crosshair, Save, RotateCcw, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import api from '@/services/apiClient'

const THINKING_LEVELS = ['minimal', 'low', 'medium', 'high']

const THINKING_COLORS = {
  minimal: 'text-text-muted',
  low: 'text-blue-400',
  medium: 'text-accent',
  high: 'text-secondary-accent',
}

export default function ProjectAISettings({ projectId }) {
  const [settings, setSettings] = useState(null)
  const [models, setModels] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [calibrating, setCalibrating] = useState(false)
  const [calibrationResult, setCalibrationResult] = useState(null)
  const [dirty, setDirty] = useState(false)
  const [localOverrides, setLocalOverrides] = useState({})
  const [statusMessage, setStatusMessage] = useState(null)

  const fetchSettings = useCallback(async () => {
    try {
      const [settingsRes, modelsRes] = await Promise.all([
        api.get(`/projects/${projectId}/settings`),
        api.get('/projects/models/available'),
      ])
      setSettings(settingsRes.data)
      setModels(modelsRes.data)
      setLocalOverrides(settingsRes.data.overrides || {})
      setDirty(false)
    } catch (e) {
      console.error('Failed to load settings:', e)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => { fetchSettings() }, [fetchSettings])

  const handleChange = (field, value) => {
    setLocalOverrides(prev => ({ ...prev, [field]: value === '' ? null : value }))
    setDirty(true)
    setStatusMessage(null)
  }

  const handleSave = async () => {
    setSaving(true)
    setStatusMessage(null)
    try {
      await api.patch(`/projects/${projectId}/settings`, localOverrides)
      await fetchSettings()
      setStatusMessage({ type: 'success', text: 'SETTINGS_SAVED' })
    } catch (e) {
      setStatusMessage({ type: 'error', text: e.response?.data?.detail || 'SAVE_FAILED' })
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    if (settings) {
      setLocalOverrides(settings.overrides || {})
      setDirty(false)
      setStatusMessage(null)
    }
  }

  const handleCalibrate = async () => {
    setCalibrating(true)
    setCalibrationResult(null)
    try {
      const res = await api.post(`/projects/${projectId}/calibrate-threshold`)
      setCalibrationResult(res.data)
      await fetchSettings()
      setStatusMessage({ type: 'success', text: `THRESHOLD_CALIBRATED: ${res.data.calibrated_threshold}` })
    } catch (e) {
      const detail = e.response?.data?.detail || 'CALIBRATION_FAILED'
      setCalibrationResult({ error: detail })
      setStatusMessage({ type: 'error', text: detail })
    } finally {
      setCalibrating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 font-mono">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
        <span className="ml-4 text-secondary-accent tracking-widest animate-pulse">LOADING_CONFIG...</span>
      </div>
    )
  }

  if (!settings || !models) {
    return <div className="text-destructive font-mono text-center py-12">ERROR: FAILED_TO_LOAD_CONFIG</div>
  }

  const effectiveValues = settings.effective || {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="w-5 h-5 text-accent" />
          <h2 className="text-lg font-bold text-text uppercase tracking-widest">AI_CONFIG</h2>
        </div>
        <div className="flex items-center gap-2">
          {dirty && (
            <button onClick={handleReset} className="flex items-center gap-1 px-3 py-1.5 text-xs text-text-muted hover:text-text border border-border hover:border-accent/50 transition-all">
              <RotateCcw className="w-3 h-3" /> RESET
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={!dirty || saving}
            className={`flex items-center gap-1 px-4 py-1.5 text-xs font-bold uppercase tracking-wider transition-all ${
              dirty ? 'bg-accent text-bg hover:bg-accent/80' : 'bg-surface text-text-muted cursor-not-allowed border border-border'
            }`}
          >
            {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
            {saving ? 'SAVING...' : 'COMMIT'}
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className={`flex items-center gap-2 px-4 py-2 text-xs font-mono border ${
          statusMessage.type === 'success' ? 'text-accent border-accent/40 bg-accent/5' : 'text-destructive border-destructive/40 bg-destructive/5'
        }`}>
          {statusMessage.type === 'success' ? <CheckCircle className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
          {statusMessage.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Language Matrix */}
        <SettingsSection icon={<Globe className="w-4 h-4" />} title="LANGUAGE_MATRIX">
          <div className="grid grid-cols-2 gap-4">
            <FieldGroup label="SOURCE_LANG">
              <select
                value={localOverrides.source_language || 'en'}
                onChange={e => handleChange('source_language', e.target.value)}
                className="w-full bg-bg border border-accent/30 text-text px-3 py-2 text-xs font-mono focus:border-accent focus:outline-none"
              >
                {(models.languages?.source || []).map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name} ({lang.code})</option>
                ))}
              </select>
            </FieldGroup>
            <FieldGroup label="TARGET_LANG">
              <select
                value={localOverrides.target_language || 'ru'}
                onChange={e => handleChange('target_language', e.target.value)}
                className="w-full bg-bg border border-accent/30 text-text px-3 py-2 text-xs font-mono focus:border-accent focus:outline-none"
              >
                {(models.languages?.target || []).map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name} ({lang.code})</option>
                ))}
              </select>
            </FieldGroup>
          </div>
        </SettingsSection>

        {/* Model Routing */}
        <SettingsSection icon={<Brain className="w-4 h-4" />} title="MODEL_ROUTING">
          {['extraction', 'translation', 'summarization'].map(task => (
            <FieldGroup key={task} label={task.toUpperCase()}>
              <select
                value={localOverrides[`model_${task}`] || ''}
                onChange={e => handleChange(`model_${task}`, e.target.value)}
                className="w-full bg-bg border border-accent/30 text-text px-3 py-2 text-xs font-mono focus:border-accent focus:outline-none"
              >
                <option value="">↳ DEFAULT ({models.defaults?.[task]})</option>
                {(models.generation_models || []).map(m => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </FieldGroup>
          ))}
        </SettingsSection>

        {/* Thinking Level */}
        <SettingsSection icon={<Zap className="w-4 h-4" />} title="THINKING_LEVEL">
          {['extraction', 'translation'].map(task => (
            <FieldGroup key={task} label={task.toUpperCase()}>
              <div className="flex gap-1">
                <button
                  onClick={() => handleChange(`thinking_${task}`, null)}
                  className={`px-2 py-1.5 text-[10px] font-bold uppercase border transition-all ${
                    !localOverrides[`thinking_${task}`]
                      ? 'bg-accent/20 text-accent border-accent/60'
                      : 'text-text-muted border-border hover:border-accent/30'
                  }`}
                >
                  DEFAULT
                </button>
                {THINKING_LEVELS.map(lvl => (
                  <button
                    key={lvl}
                    onClick={() => handleChange(`thinking_${task}`, lvl)}
                    className={`px-2 py-1.5 text-[10px] font-bold uppercase border transition-all ${
                      localOverrides[`thinking_${task}`] === lvl
                        ? `bg-accent/20 ${THINKING_COLORS[lvl]} border-accent/60`
                        : 'text-text-muted border-border hover:border-accent/30'
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </FieldGroup>
          ))}
        </SettingsSection>

        {/* Embedding Calibration */}
        <SettingsSection icon={<Crosshair className="w-4 h-4" />} title="EMBEDDING_TUNING">
          <FieldGroup label="SIMILARITY_THRESHOLD">
            <div className="flex items-center gap-3">
              <span className="text-accent text-lg font-bold font-mono">
                {localOverrides.embedding_threshold ?? effectiveValues.embedding_threshold ?? '0.75'}
              </span>
              <button
                onClick={handleCalibrate}
                disabled={calibrating}
                className="flex items-center gap-1 px-3 py-1.5 text-[10px] font-bold uppercase border border-secondary-accent/40 text-secondary-accent hover:bg-secondary-accent/10 transition-all disabled:opacity-50"
                title="Requires ≥5 approved terms with embeddings"
              >
                {calibrating ? <Loader2 className="w-3 h-3 animate-spin" /> : <Crosshair className="w-3 h-3" />}
                {calibrating ? 'CALIBRATING...' : 'AUTO_CALIBRATE'}
              </button>
            </div>
          </FieldGroup>

          {calibrationResult && !calibrationResult.error && (
            <div className="mt-3 p-3 border border-accent/20 bg-accent/5 text-[10px] font-mono space-y-1">
              <div className="text-accent font-bold">CALIBRATION_REPORT</div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-text-muted">
                <span>TERMS_ANALYZED:</span><span className="text-text">{calibrationResult.terms_analyzed}</span>
                <span>PAIRS_COMPUTED:</span><span className="text-text">{calibrationResult.pairs_computed}</span>
                <span>MIN_SIM:</span><span className="text-text">{calibrationResult.stats?.min_similarity}</span>
                <span>MAX_SIM:</span><span className="text-text">{calibrationResult.stats?.max_similarity}</span>
                <span>MEAN_SIM:</span><span className="text-text">{calibrationResult.stats?.mean_similarity}</span>
                <span>MEDIAN_SIM:</span><span className="text-text">{calibrationResult.stats?.median_similarity}</span>
              </div>
            </div>
          )}

          <p className="text-[10px] text-text-muted mt-2">
            ⓘ Requires ≥5 approved terms with embeddings. Computes optimal threshold from pairwise similarity distribution.
          </p>
        </SettingsSection>
      </div>
    </div>
  )
}

function SettingsSection({ icon, title, children }) {
  return (
    <div className="border border-accent/20 bg-surface/20 p-4 space-y-3">
      <div className="flex items-center gap-2 text-accent text-[10px] font-bold uppercase tracking-widest border-b border-accent/10 pb-2">
        {icon}
        {title}
      </div>
      {children}
    </div>
  )
}

function FieldGroup({ label, children }) {
  return (
    <div className="space-y-1">
      <label className="text-[10px] text-text-muted uppercase tracking-widest">{label}</label>
      {children}
    </div>
  )
}
