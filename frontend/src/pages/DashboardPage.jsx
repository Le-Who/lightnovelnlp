import React, { useEffect, useState } from 'react'
import api from '../services/apiClient'
import ProjectList from '../components/ProjectList.jsx'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Label } from '../components/ui/Label'
import { Spinner } from '../components/ui/Spinner'
import { Plus } from 'lucide-react'
import { useThemeView } from '../hooks/useThemeView'

export default function DashboardPage() {
  const [projects, setProjects] = useState([])
  const [name, setName] = useState('')
  const [genre, setGenre] = useState('')
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)

  // Theme View Resolver
  const Views = useThemeView();

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.get('/projects/')
      setProjects(Array.isArray(res.data) ? res.data : [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const createProject = async (e, localName, localGenre) => {
    // If called from a form event (default view), separate logic
    // If called from Neon view, args are passed directly
    if (e && e.preventDefault) e.preventDefault();

    const pName = localName || name;
    const pGenre = localGenre || genre;

    if (!pName.trim()) return

    setCreating(true)
    try {
      await api.post('/projects/', { name: pName, genre: pGenre || 'other' })
      setName('')
      setGenre('')
      load()
    } catch (e) {
      console.error(e)
      alert('Ошибка создания проекта')
    } finally {
      setCreating(false)
    }
  }



  // Default View (Original)
  return (
    <>
      {Views.Dashboard ? (
        <Views.Dashboard
          projects={projects}
          onCreateProject={(n, g) => createProject(null, n, g)}
          loading={loading}
          creating={creating}
        />
      ) : (
        <div className="space-y-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-3xl font-bold tracking-tight text-foreground">Проекты</h2>
              <p className="text-muted-foreground">Управляйте вашими переводами новелл</p>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Создать новый проект</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={(e) => createProject(e)} className="flex flex-col md:flex-row gap-4 items-end">
                <div className="grid w-full gap-1.5">
                  <Label htmlFor="project-name">Название</Label>
                  <Input
                    id="project-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Например: Overlord"
                  />
                </div>

                <div className="grid w-full gap-1.5">
                  <Label htmlFor="project-genre">Жанр</Label>
                  <Input
                    id="project-genre"
                    list="genreOptions"
                    value={genre}
                    onChange={(e) => setGenre(e.target.value)}
                    placeholder="Выберите или введите..."
                  />
                  <datalist id="genreOptions">
                    <option value="fantasy">Фантастика</option>
                    <option value="scifi">Научная фантастика</option>
                    <option value="romance">Романтика</option>
                    <option value="action">Боевик</option>
                    <option value="mystery">Детектив/Мистерия</option>
                    <option value="horror">Ужасы</option>
                    <option value="slice_of_life">Повседневность</option>
                    <option value="adventure">Приключения</option>
                    <option value="wuxia">Wuxia (Китайское боевое фэнтези)</option>
                    <option value="xianxia">Xianxia (Культивация бессмертия)</option>
                    <option value="litrpg">LitRPG (Игровые механики)</option>
                    <option value="isekai">Isekai (Попаданцы)</option>
                    <option value="other">Другое</option>
                  </datalist>
                </div>

                <Button type="submit" disabled={creating}>
                  {creating ? <Spinner className="mr-2" /> : <Plus className="mr-2 h-4 w-4" />}
                  {creating ? 'Создание...' : 'Создать'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {loading ? (
            <div className="flex justify-center py-12">
              <Spinner className="h-8 w-8 text-muted-foreground" />
            </div>
          ) : (
            <ProjectList projects={projects} />
          )}
        </div>
      }
    </>
  )
}
