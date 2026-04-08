import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Activity } from 'lucide-react'
import { TermFrequencySparkline } from '../components/analytics/TermFrequencySparkline'
import { KnowledgeGraphVisualizer } from '../components/analytics/KnowledgeGraphVisualizer'
import { ContradictionDashboard } from '../components/analytics/ContradictionDashboard'
import { NarrativeThreadEditor } from '../components/analytics/NarrativeThreadEditor'

export default function ProjectAnalyticsPage() {
  const { projectId } = useParams()

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center">
          <Link to={`/projects/${projectId}`} className="mr-4 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
              <Activity className="w-6 h-6 mr-3 text-indigo-500" />
              Project Analytics
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">MemPalace Temporal Knowledge Graph & Narrative Tracking</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 space-y-6">
          <KnowledgeGraphVisualizer projectId={projectId} />
          <TermFrequencySparkline projectId={projectId} />
        </div>
        <div className="space-y-6">
          <ContradictionDashboard projectId={projectId} />
          <NarrativeThreadEditor projectId={projectId} />
        </div>
      </div>
    </div>
  )
}
