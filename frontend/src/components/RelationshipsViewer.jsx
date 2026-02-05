import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'

export default function RelationshipsViewer({ projectId }) {
  const [relationships, setRelationships] = useState([])
  const [terms, setTerms] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedTerm, setSelectedTerm] = useState(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [termsRes, relationshipsRes] = await Promise.all([
        api.get(`/glossary/${projectId}/terms`),
        api.get(`/glossary/${projectId}/relationships`)
      ])
      setTerms(termsRes.data)
      setRelationships(relationshipsRes.data)
    } catch (e) {
      console.error('Error loading relationships:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      loadData()
    }
  }, [projectId])

  const getTermById = (id) => terms.find(term => term.id === id)

  const getRelationTypeLabel = (type) => {
    const labels = {
      'friend': 'Друзья',
      'enemy': 'Враги',
      'family': 'Семья',
      'location': 'Локация',
      'skill_related': 'Связанные умения',
      'artifact_owner': 'Владелец артефакта',
      'teacher_student': 'Учитель-ученик',
      'rival': 'Соперники',
      'ally': 'Союзники',
      'other': 'Другие связи'
    }
    return labels[type] || type
  }

  const getRelationTypeColor = (type) => {
    const colors = {
      'friend': '#4CAF50',
      'enemy': '#f44336',
      'family': '#2196F3',
      'location': '#FF9800',
      'skill_related': '#9C27B0',
      'artifact_owner': '#795548',
      'teacher_student': '#607D8B',
      'rival': '#E91E63',
      'ally': '#00BCD4',
      'other': '#9E9E9E'
    }
    return colors[type] || '#9E9E9E'
  }

  if (loading) return <div>Загрузка связей...</div>

  if (relationships.length === 0) {
    return (
      <div>
        <h3>Связи между терминами</h3>
        <p>Связи отсутствуют. Запустите анализ глав для выявления связей между терминами.</p>
      </div>
    )
  }

  return (
    <div>
      <h3>Связи между терминами</h3>
      
      {/* Фильтр по термину */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ marginRight: 8 }}>Фильтр по термину:</label>
        <select 
          value={selectedTerm || ''} 
          onChange={(e) => setSelectedTerm(e.target.value || null)}
          style={{ padding: 4 }}
        >
          <option value="">Все связи</option>
          {terms.map(term => (
            <option key={term.id} value={term.id}>
              {term.source_term} → {term.translated_term}
            </option>
          ))}
        </select>
      </div>

      {/* Список связей */}
      <div style={{ display: 'grid', gap: 16 }}>
        {relationships
          .filter(rel => {
            if (!selectedTerm) return true
            return rel.source_term_id === parseInt(selectedTerm) || 
                   rel.target_term_id === parseInt(selectedTerm)
          })
          .map((relationship) => {
            const sourceTerm = getTermById(relationship.source_term_id)
            const targetTerm = getTermById(relationship.target_term_id)
            
            if (!sourceTerm || !targetTerm) return null
            
            return (
              <div 
                key={relationship.id} 
                style={{ 
                  border: '1px solid #ddd', 
                  padding: 16, 
                  borderRadius: 8,
                  borderLeft: `4px solid ${getRelationTypeColor(relationship.relation_type)}`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
                      <strong>{sourceTerm.source_term}</strong>
                      <span style={{ color: 'gray' }}>→</span>
                      <strong>{targetTerm.source_term}</strong>
                    </div>
                    
                    <div style={{ display: 'flex', gap: 16, fontSize: '0.9em', color: '#666', marginBottom: 8 }}>
                      <span style={{ 
                        color: getRelationTypeColor(relationship.relation_type),
                        fontWeight: 'bold'
                      }}>
                        {getRelationTypeLabel(relationship.relation_type)}
                      </span>
                      {relationship.confidence && (
                        <span>Уверенность: {relationship.confidence}%</span>
                      )}
                    </div>
                    
                    <div style={{ fontSize: '0.9em', color: '#666', marginBottom: 8 }}>
                      <strong>Переводы:</strong> {sourceTerm.translated_term} → {targetTerm.translated_term}
                    </div>
                    
                    {relationship.context && (
                      <div style={{ fontSize: '0.9em', color: '#666' }}>
                        <strong>Контекст:</strong> {relationship.context}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
      </div>
    </div>
  )
}
