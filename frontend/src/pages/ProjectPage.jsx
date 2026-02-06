import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Book, Share2, Languages, History, Layers, FileText, Edit2 } from 'lucide-react'
import api from '../services/apiClient'
import ChapterManager from '../components/ChapterManager.jsx'
import GlossaryEditor from '../components/GlossaryEditor.jsx'
import ChapterViewer from '../components/ChapterViewer.jsx'
import RelationshipsViewer from '../components/RelationshipsViewer.jsx'
import GlossaryVersionManager from '../components/GlossaryVersionManager.jsx'
import BatchProcessor from '../components/BatchProcessor.jsx'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/Tabs'
import { Spinner } from '../components/ui/Spinner'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Label } from '../components/ui/Label'
import { Modal } from '../components/ui/Modal'
import { useThemeView } from '../hooks/useThemeView'

export default function ProjectPage() {
  const { projectId } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [editFormData, setEditFormData] = useState({ name: '', genre: '' })
  const [updating, setUpdating] = useState(false)

  // Theme View Resolver
  const Views = useThemeView();

  const loadProject = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/projects/${projectId}`)
      setProject(res.data)
    } catch (e) {
      console.error('Error loading project:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      loadProject()
    }
  }, [projectId])

  const openEditModal = () => {
    setEditFormData({ name: project.name, genre: project.genre || '' })
    setIsEditModalOpen(true)
  }

  const handleUpdateProject = async () => {
    if (!editFormData.name.trim()) return

    setUpdating(true)
    try {
      await api.put(`/projects/${projectId}`, editFormData)
      await loadProject()
      setIsEditModalOpen(false)
    } catch (e) {
      console.error('Error updating project:', e)
      alert('Ошибка обновления проекта')
    } finally {
      setUpdating(false)
    }
  }

  if (Views.ProjectPage) {
    return (
      <Views.ProjectPage
        project={project}
        loading={loading}
        projectId={projectId}
        refresh={loadProject}
      />
    );
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
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight text-foreground">{project.name}</h1>
              <Button variant="ghost" size="icon" onClick={openEditModal} title="Редактировать проект">
                <Edit2 className="h-5 w-5 text-muted-foreground hover:text-foreground" />
              </Button>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
               <span className="capitalize bg-muted px-2 py-0.5 rounded text-sm">{project.genre || 'Other'}</span>
               <span>•</span>
               <span>Создан: {new Date(project.created_at).toLocaleDateString()}</span>
            </div>
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
      </Tabs>

      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Редактировать проект"
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-name">Название проекта</Label>
            <Input
              id="edit-name"
              value={editFormData.name}
              onChange={(e) => setEditFormData(prev => ({ ...prev, name: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-genre">Жанр</Label>
            <Input
              id="edit-genre"
              value={editFormData.genre}
              onChange={(e) => setEditFormData(prev => ({ ...prev, genre: e.target.value }))}
              placeholder="Фантастика, Isekai и т.д."
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setIsEditModalOpen(false)} disabled={updating}>
              Отмена
            </Button>
            <Button onClick={handleUpdateProject} disabled={updating}>
              {updating ? <Spinner className="mr-2 h-4 w-4" /> : null}
              Сохранить
            </Button>
          </div>
        </div>
      </Modal>
    </div >
  )
}
