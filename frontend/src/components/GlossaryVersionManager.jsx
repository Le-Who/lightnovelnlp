import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { Textarea } from './ui/Textarea'
import { Label } from './ui/Label'
import { Spinner } from './ui/Spinner'
import { History, Save, RefreshCw } from 'lucide-react'

export default function GlossaryVersionManager({ projectId }) {
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(false)
  const [creatingVersion, setCreatingVersion] = useState(false)
  const [newVersionName, setNewVersionName] = useState('')
  const [newVersionDescription, setNewVersionDescription] = useState('')

  const loadVersions = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/glossary/${projectId}/versions`)
      setVersions(res.data)
    } catch (e) {
      console.error('Error loading versions:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      loadVersions()
    }
  }, [projectId])

  const createVersion = async () => {
    if (!newVersionName.trim()) {
      alert('Введите название версии')
      return
    }

    setCreatingVersion(true)
    try {
      await api.post(`/glossary/${projectId}/versions`, {
        name: newVersionName,
        description: newVersionDescription
      })
      
      setNewVersionName('')
      setNewVersionDescription('')
      loadVersions()
      alert('Версия создана успешно!')
    } catch (e) {
      console.error('Error creating version:', e)
      alert('Ошибка при создании версии')
    } finally {
      setCreatingVersion(false)
    }
  }

  const restoreVersion = async (versionId) => {
    if (!confirm('Вы уверены, что хотите восстановить эту версию? Текущий глоссарий будет заменен.')) {
      return
    }

    try {
      await api.post(`/glossary/versions/${versionId}/restore`)
      alert('Глоссарий восстановлен успешно!')
      window.location.reload()
    } catch (e) {
      console.error('Error restoring version:', e)
      alert('Ошибка при восстановлении версии')
    }
  }

  if (loading) return <div className="flex justify-center p-8"><Spinner /></div>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Создать новую версию</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="version-name">Название версии</Label>
            <Input
              id="version-name"
              value={newVersionName}
              onChange={(e) => setNewVersionName(e.target.value)}
              placeholder="Например: Версия 1.0"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="version-desc">Описание</Label>
            <Textarea
              id="version-desc"
              value={newVersionDescription}
              onChange={(e) => setNewVersionDescription(e.target.value)}
              placeholder="Описание изменений в этой версии"
              rows={4}
            />
          </div>
          
          <Button
            onClick={createVersion}
            disabled={creatingVersion}
            className="w-full"
          >
            {creatingVersion ? <Spinner className="mr-2" /> : <Save className="mr-2 h-4 w-4" />}
            {creatingVersion ? 'Создание...' : 'Создать версию'}
          </Button>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h3 className="text-xl font-semibold tracking-tight">История версий</h3>
        {versions.length === 0 ? (
          <div className="text-center py-12 border border-dashed rounded-lg text-slate-500">
            Версии отсутствуют.
          </div>
        ) : (
          <div className="space-y-4">
            {versions.map((version) => (
              <Card key={version.version_id}>
                <CardContent className="p-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <History className="h-4 w-4 text-slate-500" />
                        <h4 className="font-semibold">
                          {version.name || `Версия ${version.version_number}`}
                        </h4>
                      </div>
                      <div className="text-sm text-slate-500">
                        {new Date(version.created_at).toLocaleString()}
                      </div>
                      {version.description && (
                        <p className="text-sm text-slate-600 mt-2">
                          {version.description}
                        </p>
                      )}
                      <div className="flex gap-4 mt-2 text-xs text-slate-500">
                        <span>Терминов: {version.terms_count}</span>
                        <span>Утверждено: {version.approved_terms_count}</span>
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => restoreVersion(version.version_id)}
                    >
                      <RefreshCw className="mr-2 h-3 w-3" />
                      Восстановить
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
