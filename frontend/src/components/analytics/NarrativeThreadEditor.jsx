import React, { useState, useEffect } from 'react'
import api from '../../services/apiClient'
import { GitCommit, Plus, GitBranch } from 'lucide-react'

export function NarrativeThreadEditor({ projectId }) {
  const [threads, setThreads] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchThreads = async () => {
      try {
        const res = await api.get(`/graph/${projectId}/analytics/threads`)
        if (res.data?.threads) {
          setThreads(res.data.threads)
        }
      } catch (err) {
        console.error("Failed to load threads", err)
      } finally {
        setLoading(false)
      }
    }
    fetchThreads()
  }, [projectId])

  if (loading) return <div className="p-4 text-gray-500">Loading narrative threads...</div>

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-800/50">
        <h3 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center">
          <GitBranch className="w-5 h-5 mr-2 text-indigo-500" />
          Narrative Threads
        </h3>
        <button className="text-sm bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-3 py-1.5 rounded-lg flex items-center hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors">
          <Plus className="w-4 h-4 mr-1" /> New Thread
        </button>
      </div>
      
      {threads.length === 0 ? (
        <div className="p-8 text-center text-gray-500 text-sm">
          No narrative threads tracked yet.<br/>
          Threads link plot points across chapters automatically based on term co-occurrence.
        </div>
      ) : (
        <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-96 overflow-y-auto p-4">
          {threads.map(thread => (
            <div key={thread.id} className="py-4 first:pt-0 last:pb-0">
              <div className="flex justify-between mb-3">
                <h4 className="font-medium text-gray-800 dark:text-gray-200">{thread.title}</h4>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  thread.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                  thread.status === 'resolved' ? 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300' :
                  'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                }`}>
                  {thread.status}
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{thread.description}</p>
              
              <div className="relative pl-4 space-y-4 border-l-2 border-gray-200 dark:border-gray-700 ml-2">
                {thread.anchors?.map(anchor => (
                  <div key={anchor.id} className="relative">
                    <div className="absolute -left-[25px] top-1 bg-white dark:bg-gray-800 rounded-full">
                      <GitCommit className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                    </div>
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300">Chapter {anchor.chapter_id}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">{anchor.summary_snippet}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
