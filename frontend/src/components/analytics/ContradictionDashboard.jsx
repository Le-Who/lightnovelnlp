import React, { useState, useEffect } from 'react'
import api from '../../services/apiClient'
import { AlertCircle, CheckCircle2 } from 'lucide-react'

export function ContradictionDashboard({ projectId }) {
  const [contradictions, setContradictions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchContradictions = async () => {
      try {
        const res = await api.get(`/graph/${projectId}/contradictions`)
        if (res.data?.contradictions) {
          setContradictions(res.data.contradictions)
        }
      } catch (err) {
        console.error("Failed to load contradictions", err)
      } finally {
        setLoading(false)
      }
    }
    fetchContradictions()
  }, [projectId])

  if (loading) return <div className="p-4 text-gray-500">Scanning for contradictions...</div>

  if (contradictions.length === 0) {
    return (
      <div className="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl flex items-center shadow-sm">
        <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400 mr-3" />
        <span className="text-green-800 dark:text-green-300 font-medium">Knowledge Graph is consistent. No contradictions detected.</span>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-red-200 dark:border-red-900/50 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 bg-red-50 dark:bg-red-900/20 border-b border-red-100 dark:border-red-900/30 flex items-center">
        <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2" />
        <h3 className="font-semibold text-red-800 dark:text-red-300">Contradictions Detected ({contradictions.length})</h3>
      </div>
      <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-96 overflow-y-auto">
        {contradictions.map((c, i) => (
          <div key={i} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
            <div className="flex justify-between items-start mb-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300">
                {c.conflict_type} Group: {c.group_name}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mt-3">
              <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="text-xs text-gray-500 mb-1">Relationship 1 (Chap {c.rel1.source_chapter_id || '?'})</div>
                <div className="font-medium text-sm text-gray-800 dark:text-gray-200">
                  {c.rel1.source_term} <span className="text-blue-500">→ {c.rel1.relation_type} →</span> {c.rel1.target_term}
                </div>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="text-xs text-gray-500 mb-1">Relationship 2 (Chap {c.rel2.source_chapter_id || '?'})</div>
                <div className="font-medium text-sm text-gray-800 dark:text-gray-200">
                  {c.rel2.source_term} <span className="text-amber-500">→ {c.rel2.relation_type} →</span> {c.rel2.target_term}
                </div>
              </div>
            </div>
            <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
              <p>These relationships violate the mutual exclusivity rule for the <strong>{c.group_name}</strong> category simultaneously.</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
