import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'
import { Spinner } from './ui/Spinner'
import { Alert, AlertTitle, AlertDescription } from './ui/Alert'
import { Play, XCircle, RefreshCw } from 'lucide-react'

export default function BatchProcessor({ projectId }) {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [creatingJob, setCreatingJob] = useState(false)
  const [activeJobs, setActiveJobs] = useState(new Set())

  const loadJobs = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/batch/${projectId}/jobs`)
      setJobs(res.data)
      
      const active = new Set()
      res.data.forEach(job => {
        if (job.status === 'pending' || job.status === 'running') {
          active.add(job.id)
        }
      })
      setActiveJobs(active)
    } catch (e) {
      console.error('Error loading jobs:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      loadJobs()
    }
  }, [projectId])

  useEffect(() => {
    if (activeJobs.size === 0) return

    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/batch/${projectId}/jobs`)
        setJobs(res.data)
        
        const stillActive = new Set()
        res.data.forEach(job => {
          if (job.status === 'pending' || job.status === 'running') {
            stillActive.add(job.id)
          }
        })
        setActiveJobs(stillActive)
        
        if (stillActive.size === 0) {
          clearInterval(interval)
        }
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
      alert('Задача анализа создана!')
    } catch (e) {
      console.error('Error creating analyze job:', e)
      alert('Ошибка при создании задачи анализа')
    } finally {
      setCreatingJob(false)
    }
  }

  const createTranslateJob = async () => {
    setCreatingJob(true)
    try {
      await api.post(`/batch/${projectId}/translate-chapters`, {})
      loadJobs()
      alert('Задача перевода создана!')
    } catch (e) {
      console.error('Error creating translate job:', e)
      alert('Ошибка при создании задачи перевода')
    } finally {
      setCreatingJob(false)
    }
  }

  const cancelJob = async (jobId) => {
    if (!confirm('Вы уверены, что хотите отменить эту задачу?')) {
      return
    }

    try {
      await api.delete(`/batch/jobs/${jobId}`)
      loadJobs()
      alert('Задача отменена!')
    } catch (e) {
      console.error('Error cancelling job:', e)
      alert('Ошибка при отмене задачи')
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed': return <Badge variant="success">Завершено</Badge>
      case 'running': return <Badge variant="info">Выполняется</Badge>
      case 'pending': return <Badge variant="warning">Ожидает</Badge>
      case 'failed': return <Badge variant="destructive">Ошибка</Badge>
      case 'cancelled': return <Badge variant="secondary">Отменено</Badge>
      default: return <Badge variant="outline">{status}</Badge>
    }
  }

  const getJobTypeLabel = (jobType) => {
    switch (jobType) {
      case 'analyze': return 'Анализ глав'
      case 'translate': return 'Перевод глав'
      default: return jobType
    }
  }

  if (loading && jobs.length === 0) return <div className="flex justify-center p-8"><Spinner /></div>

  return (
    <div className="space-y-6">
      <Card className="bg-muted/50 border-dashed">
        <CardHeader>
          <CardTitle>Создать задачу</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 mb-4">
            <Button
              onClick={createAnalyzeJob}
              disabled={creatingJob}
              className="bg-green-600 hover:bg-green-700 dark:text-white"
            >
              {creatingJob ? <Spinner className="mr-2" /> : <Play className="mr-2 h-4 w-4" />}
              Анализ всех глав
            </Button>

            <Button
              onClick={createTranslateJob}
              disabled={creatingJob}
              className="bg-blue-600 hover:bg-blue-700 dark:text-white"
            >
              {creatingJob ? <Spinner className="mr-2" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              Перевод всех глав
            </Button>
          </div>
          
          <div className="text-sm text-muted-foreground space-y-1">
            <p><strong>Анализ глав:</strong> Извлечение терминов, анализ связей, создание саммари</p>
            <p><strong>Перевод глав:</strong> Перевод всех непереведенных глав с использованием глоссария</p>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h3 className="text-xl font-semibold tracking-tight text-foreground">История задач</h3>
        {jobs.length === 0 ? (
          <div className="text-center py-12 border border-dashed rounded-lg text-muted-foreground">
            Задачи отсутствуют.
          </div>
        ) : (
          <div className="grid gap-4">
            {jobs.map((job) => (
              <Card key={job.id} className="overflow-hidden">
                <CardContent className="p-4">
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-3">
                         <h4 className="font-semibold text-card-foreground">{getJobTypeLabel(job.job_type)}</h4>
                         {getStatusBadge(job.status)}
                      </div>

                      <div className="text-xs text-muted-foreground flex gap-4">
                        <span>Создана: {new Date(job.created_at).toLocaleString()}</span>
                        {job.started_at && <span>Начата: {new Date(job.started_at).toLocaleString()}</span>}
                        {job.completed_at && <span>Завершена: {new Date(job.completed_at).toLocaleString()}</span>}
                      </div>

                      <div className="text-sm font-medium mt-2 text-card-foreground">
                        Прогресс: {job.progress_percentage}%
                        <span className="text-muted-foreground/70 font-normal ml-2">
                          ({job.processed_items} / {job.total_items})
                        </span>
                      </div>

                      {/* Simple Progress Bar */}
                      <div className="w-full h-2 bg-secondary rounded-full overflow-hidden max-w-md mt-1">
                        <div
                          className={`h-full transition-all duration-500 ${job.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'}`}
                          style={{ width: `${job.progress_percentage}%` }}
                        />
                      </div>

                      {job.failed_items > 0 && (
                        <div className="text-xs text-red-500 font-medium">
                          Ошибок: {job.failed_items}
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col gap-2 items-end">
                      {(job.status === 'pending' || job.status === 'running') && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => cancelJob(job.id)}
                        >
                          <XCircle className="mr-2 h-4 w-4" />
                          Отменить
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {job.error_message && (
                    <Alert variant="destructive" className="mt-4">
                      <AlertTitle>Ошибка</AlertTitle>
                      <AlertDescription>{job.error_message}</AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
