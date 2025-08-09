import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'

export default function GlossaryEditor({ projectId }) {
  const [terms, setTerms] = useState([])
  const [loading, setLoading] = useState(false)
  const [editingTerm, setEditingTerm] = useState(null)

  const loadTerms = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/glossary/${projectId}/terms`)
      setTerms(res.data)
    } catch (e) {
      console.error('Error loading terms:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      loadTerms()
    }
  }, [projectId])

  const approveTerm = async (termId) => {
    try {
      await api.post(`/glossary/terms/${termId}/approve`)
      loadTerms() // Перезагружаем список
    } catch (e) {
      console.error('Error approving term:', e)
      alert('Ошибка утверждения термина')
    }
  }

  const updateTerm = async (termId, updates) => {
    try {
      await api.put(`/glossary/terms/${termId}`, updates)
      setEditingTerm(null)
      loadTerms()
    } catch (e) {
      console.error('Error updating term:', e)
      alert('Ошибка обновления термина')
    }
  }

  const deleteTerm = async (termId) => {
    if (!confirm('Удалить этот термин?')) return
    
    try {
      await api.delete(`/glossary/terms/${termId}`)
      loadTerms()
    } catch (e) {
      console.error('Error deleting term:', e)
      alert('Ошибка удаления термина')
    }
  }

  const getStatusColor = (status) => {
    return status === 'approved' ? 'green' : 'orange'
  }

  const getCategoryLabel = (category) => {
    const labels = {
      character: 'Персонаж',
      location: 'Локация', 
      skill: 'Умение',
      artifact: 'Артефакт',
      other: 'Другое'
    }
    return labels[category] || category
  }

  if (loading) return <div>Загрузка глоссария...</div>

  return (
    <div>
      <h3>Глоссарий проекта</h3>
      {terms.length === 0 ? (
        <p>Термины отсутствуют. Запустите анализ главы для извлечения терминов.</p>
      ) : (
        <div style={{ display: 'grid', gap: 16 }}>
          {terms.map((term) => (
            <div 
              key={term.id} 
              style={{ 
                border: '1px solid #ddd', 
                padding: 16, 
                borderRadius: 8,
                backgroundColor: term.status === 'approved' ? '#f0f8f0' : '#fff8f0'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
                    <strong>{term.source_term}</strong>
                    <span style={{ color: 'gray' }}>→</span>
                    {editingTerm?.id === term.id ? (
                      <input
                        value={editingTerm.translated_term}
                        onChange={(e) => setEditingTerm({
                          ...editingTerm,
                          translated_term: e.target.value
                        })}
                        style={{ flex: 1 }}
                      />
                    ) : (
                      <strong>{term.translated_term}</strong>
                    )}
                  </div>
                  
                  <div style={{ display: 'flex', gap: 16, fontSize: '0.9em', color: '#666' }}>
                    <span>Категория: {getCategoryLabel(term.category)}</span>
                    <span style={{ color: getStatusColor(term.status) }}>
                      Статус: {term.status === 'approved' ? 'Утвержден' : 'Ожидает'}
                    </span>
                  </div>
                  
                  {term.context && (
                    <div style={{ marginTop: 8, fontSize: '0.9em', color: '#666' }}>
                      <strong>Контекст:</strong> {term.context}
                    </div>
                  )}
                </div>
                
                <div style={{ display: 'flex', gap: 8 }}>
                  {editingTerm?.id === term.id ? (
                    <>
                      <button 
                        onClick={() => updateTerm(term.id, {
                          translated_term: editingTerm.translated_term
                        })}
                        style={{ padding: '4px 8px', fontSize: '0.8em' }}
                      >
                        Сохранить
                      </button>
                      <button 
                        onClick={() => setEditingTerm(null)}
                        style={{ padding: '4px 8px', fontSize: '0.8em' }}
                      >
                        Отмена
                      </button>
                    </>
                  ) : (
                    <>
                      <button 
                        onClick={() => setEditingTerm(term)}
                        style={{ padding: '4px 8px', fontSize: '0.8em' }}
                      >
                        Редактировать
                      </button>
                      {term.status === 'pending' && (
                        <button 
                          onClick={() => approveTerm(term.id)}
                          style={{ padding: '4px 8px', fontSize: '0.8em', backgroundColor: '#4CAF50', color: 'white' }}
                        >
                          Утвердить
                        </button>
                      )}
                      <button 
                        onClick={() => deleteTerm(term.id)}
                        style={{ padding: '4px 8px', fontSize: '0.8em', backgroundColor: '#f44336', color: 'white' }}
                      >
                        Удалить
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
