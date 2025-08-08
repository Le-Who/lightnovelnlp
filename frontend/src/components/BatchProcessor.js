import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'

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
      
      // Определяем активные задачи для отслеживания
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

  // Отслеживание активных задач
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
        
        // Если нет активных задач, останавливаем интервал
        if (stillActive.size === 0) {
          clearInterval(interval)
        }
      } catch (e) {
        console.error('Error updating jobs:', e)
      }
    }, 2000) // Обновляем каждые 2 секунды

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

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#4CAF50'
      case 'running': return '#2196F3'
      case 'pending': return '#FF9800'
      case 'failed': return '#f44336'
      case 'cancelled': return '#9E9E9E'
      default: return '#9E9E9E'
    }
  }

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed': return 'Завершено'
      case 'running': return 'Выполняется'
      case 'pending': return 'Ожидает'
      case 'failed': return 'Ошибка'
      case 'cancelled': return 'Отменено'
      default: return status
    }
  }

  const getJobTypeLabel = (jobType) => {
    switch (jobType) {
      case 'analyze': return 'Анализ глав'
      case 'translate': return 'Перевод глав'
      default: return jobType
    }
  }

  if (loading) return <div>Загрузка задач...</div>

  return (
    <div>
      <h3>Пакетная обработка</h3>
      
      {/* Создание задач */}
      <div style={{ 
        border: '1px solid #ddd', 
        padding: 16, 
        borderRadius: 8, 
        marginBottom: 24,
        backgroundColor: '#f9f9f9'
      }}>
        <h4 style={{ margin: '0 0 16px 0' }}>Создать задачу</h4>
        
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={createAnalyzeJob}
            disabled={creatingJob}
            style={{
              padding: '12px 24px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: creatingJob ? 'not-allowed' : 'pointer',
              opacity: creatingJob ? 0.7 : 1
            }}
          >
            {creatingJob ? 'Создание...' : 'Анализ всех глав'}
          </button>
          
          <button
            onClick={createTranslateJob}
            disabled={creatingJob}
            style={{
              padding: '12px 24px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: creatingJob ? 'not-allowed' : 'pointer',
              opacity: creatingJob ? 0.7 : 1
            }}
          >
            {creatingJob ? 'Создание...' : 'Перевод всех глав'}
          </button>
        </div>
        
        <div style={{ fontSize: '0.9em', color: '#666', marginTop: 12 }}>
          <p><strong>Анализ глав:</strong> Извлечение терминов, анализ связей, создание саммари</p>
          <p><strong>Перевод глав:</strong> Перевод всех непереведенных глав с использованием глоссария</p>
        </div>
      </div>

      {/* Список задач */}
      {jobs.length === 0 ? (
        <p>Задачи отсутствуют. Создайте первую задачу пакетной обработки.</p>
      ) : (
        <div style={{ display: 'grid', gap: 16 }}>
          {jobs.map((job) => (
            <div 
              key={job.id} 
              style={{ 
                border: '1px solid #ddd', 
                padding: 16, 
                borderRadius: 8,
                backgroundColor: 'white'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <h4 style={{ margin: '0 0 4px 0' }}>
                    {getJobTypeLabel(job.job_type)}
                  </h4>
                  <div style={{ fontSize: '0.9em', color: '#666', marginBottom: 8 }}>
                    Создана: {new Date(job.created_at).toLocaleString()}
                  </div>
                  {job.started_at && (
                    <div style={{ fontSize: '0.9em', color: '#666', marginBottom: 8 }}>
                      Начата: {new Date(job.started_at).toLocaleString()}
                    </div>
                  )}
                  {job.completed_at && (
                    <div style={{ fontSize: '0.9em', color: '#666', marginBottom: 8 }}>
                      Завершена: {new Date(job.completed_at).toLocaleString()}
                    </div>
                  )}
                </div>
                
                <div style={{ textAlign: 'right' }}>
                  <div style={{ 
                    fontSize: '0.9em', 
                    color: getStatusColor(job.status),
                    fontWeight: 'bold',
                    marginBottom: 8
                  }}>
                    {getStatusLabel(job.status)}
                  </div>
                  
                  <div style={{ fontSize: '0.8em', color: '#666', marginBottom: 4 }}>
                    Прогресс: {job.progress_percentage}%
                  </div>
                  <div style={{ fontSize: '0.8em', color: '#666', marginBottom: 4 }}>
                    Обработано: {job.processed_items} / {job.total_items}
                  </div>
                  {job.failed_items > 0 && (
                    <div style={{ fontSize: '0.8em', color: '#f44336', marginBottom: 8 }}>
                      Ошибок: {job.failed_items}
                    </div>
                  )}
                  
                  {(job.status === 'pending' || job.status === 'running') && (
                    <button
                      onClick={() => cancelJob(job.id)}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: 4,
                        cursor: 'pointer',
                        fontSize: '0.9em'
                      }}
                    >
                      Отменить
                    </button>
                  )}
                </div>
              </div>
              
              {job.error_message && (
                <div style={{ 
                  fontSize: '0.9em', 
                  color: '#f44336', 
                  backgroundColor: '#ffebee',
                  padding: 8,
                  borderRadius: 4,
                  marginTop: 8
                }}>
                  <strong>Ошибка:</strong> {job.error_message}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
