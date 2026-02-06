import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Book, Share2, Languages, History, Layers, FileText } from 'lucide-react'
import api from '../services/apiClient'
import ChapterManager from '../components/ChapterManager.jsx'
import GlossaryEditor from '../components/GlossaryEditor.jsx'
import ChapterViewer from '../components/ChapterViewer.jsx'
import RelationshipsViewer from '../components/RelationshipsViewer.jsx'
import GlossaryVersionManager from '../components/GlossaryVersionManager.jsx'
import BatchProcessor from '../components/BatchProcessor.jsx'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/Tabs'
import { Spinner } from '../components/ui/Spinner'
import { useThemeView } from '../hooks/useThemeView'

export default function ProjectPage() {
  const { projectId } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(false)

  // Theme View Resolver
  const Views = useThemeView();

  // If a specific theme view exists for ProjectPage, render it
  // Note: We need to handle data loading inside the view OR pass it down.
  // NeonProjectPage handles its own loading for now to simpler refactoring.
  useEffect(() => {
    if (projectId && !Views.ProjectPage) {
      loadProject()
    }
  }, [projectId, Views.ProjectPage])

  if (Views.ProjectPage) {
    return <Views.ProjectPage />;
  }

  if (loading) return (
    <div className="flex h-[50vh] items-center justify-center">
      <Spinner className="h-8 w-8 text-muted-foreground" />
    </div>
  )

  if (!project) return (
    <div className="flex flex-col items-center justify-center py-12">
      <h2 className="text-xl font-semibold mb-2 text-foreground">Проект не найден</h2>
      <Link to="/" className="text-primary underline-offset-4 hover:underline">
        Вернуться на главную
      </Link>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <Link
          to="/"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          Назад к проектам
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">{project.name}</h1>
            <p className="text-muted-foreground">
              Создан: {new Date(project.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      <Tabs defaultValue="chapters" className="w-full">
        <TabsList className="w-full justify-start overflow-x-auto">
          <TabsTrigger value="chapters">
            <Book className="mr-2 h-4 w-4" />
            Главы
          </TabsTrigger>
          <TabsTrigger value="glossary">
            <FileText className="mr-2 h-4 w-4" />
            Глоссарий
          </TabsTrigger>
          <TabsTrigger value="relationships">
            <Share2 className="mr-2 h-4 w-4" />
            Связи
          </TabsTrigger>
          <TabsTrigger value="translations">
            <Languages className="mr-2 h-4 w-4" />
            Переводы
          </TabsTrigger>
          <TabsTrigger value="versions">
            <History className="mr-2 h-4 w-4" />
            Версии
          </TabsTrigger>
          <TabsTrigger value="batch">
            <Layers className="mr-2 h-4 w-4" />
            Пакетная обработка
          </TabsTrigger>
        </TabsList>

        <div className="mt-6">
          <TabsContent value="chapters">
            <ChapterManager projectId={projectId} />
          </TabsContent>
          <TabsContent value="glossary">
            <GlossaryEditor projectId={projectId} />
          </TabsContent>
          <TabsContent value="relationships">
            <RelationshipsViewer projectId={projectId} />
          </TabsContent>
          <TabsContent value="translations">
            <ChapterViewer projectId={projectId} />
          </TabsContent>
          <TabsContent value="versions">
            <GlossaryVersionManager projectId={projectId} />
          </TabsContent>
          <TabsContent value="batch">
            <BatchProcessor projectId={projectId} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  )
}
