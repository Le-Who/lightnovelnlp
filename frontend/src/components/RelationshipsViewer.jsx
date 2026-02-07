import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Spinner } from './ui/Spinner'
import { ArrowRight } from 'lucide-react'

export default function RelationshipsViewer({ projectId }) {
  const [relationships, setRelationships] = useState([])
  const [terms, setTerms] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedTerm, setSelectedTerm] = useState(null)
  const [sortBy, setSortBy] = useState('confidence')

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

  const getRelationTypeColorClass = (type) => {
    const classes = {
      'friend': 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800',
      'enemy': 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800',
      'family': 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800',
      'location': 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-800',
      'skill_related': 'bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800',
      'artifact_owner': 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800',
      'teacher_student': 'bg-slate-100 text-slate-800 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
      'rival': 'bg-pink-100 text-pink-800 border-pink-200 dark:bg-pink-900/30 dark:text-pink-300 dark:border-pink-800',
      'ally': 'bg-cyan-100 text-cyan-800 border-cyan-200 dark:bg-cyan-900/30 dark:text-cyan-300 dark:border-cyan-800',
      'other': 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700'
    }
    return classes[type] || classes['other']
  }

  if (loading) return <div className="flex justify-center p-8"><Spinner /></div>

  if (relationships.length === 0) {
    return (
      <div className="text-center py-12 border border-dashed rounded-lg text-muted-foreground">
        Связи отсутствуют. Запустите анализ глав для выявления связей между терминами.
      </div>
    )
  }

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 20

  const filteredRelationships = relationships.filter(rel => {
    if (!selectedTerm) return true
    return rel.source_term_id === parseInt(selectedTerm) ||
      rel.target_term_id === parseInt(selectedTerm)
  })

  // Reset page when filter changes
  useEffect(() => {
    setCurrentPage(1)
  }, [selectedTerm, sortBy])

  const sortedRelationships = [...filteredRelationships].sort((a, b) => {
    if (sortBy === 'confidence') return (b.confidence || 0) - (a.confidence || 0)
    if (sortBy === 'source_term') {
      const termA = getTermById(a.source_term_id)?.source_term || ''
      const termB = getTermById(b.source_term_id)?.source_term || ''
      return termA.localeCompare(termB)
    }
    if (sortBy === 'target_term') {
      const termA = getTermById(a.target_term_id)?.source_term || ''
      const termB = getTermById(b.target_term_id)?.source_term || ''
      return termA.localeCompare(termB)
    }
    if (sortBy === 'category') {
      const catA = getTermById(a.source_term_id)?.category || ''
      const catB = getTermById(b.source_term_id)?.category || ''
      return catA.localeCompare(catB)
    }
    if (sortBy === 'relation_type') return a.relation_type.localeCompare(b.relation_type)
    return 0
  })

  const totalPages = Math.ceil(sortedRelationships.length / itemsPerPage)
  const paginatedRelationships = sortedRelationships.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage)
      document.querySelector('.relationships-container')?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <div className="space-y-6 relationships-container">
      <Card>
        <CardHeader className="pb-3">
          <div className="flex justify-between items-center">
            <CardTitle className="text-lg">Фильтр и Сортировка</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Термин:</label>
              <select
                value={selectedTerm || ''}
                onChange={(e) => setSelectedTerm(e.target.value || null)}
                className="h-9 w-full md:w-64 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground"
              >
                <option value="">Все связи</option>
                {terms.map(term => (
                  <option key={term.id} value={term.id}>
                    {term.source_term} → {term.translated_term}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Сортировка:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="h-9 w-full md:w-48 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground"
              >
                <option value="confidence">По уверенности</option>
                <option value="source_term">По источнику</option>
                <option value="target_term">По цели</option>
                <option value="category">По категории источника</option>
                <option value="relation_type">По типу связи</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {paginatedRelationships.map((relationship) => {
          const sourceTerm = getTermById(relationship.source_term_id)
          const targetTerm = getTermById(relationship.target_term_id)

          if (!sourceTerm || !targetTerm) return null

          return (
            <Card key={relationship.id} className="relative overflow-hidden">
              <div className={`absolute top-0 left-0 w-1 h-full ${getRelationTypeColorClass(relationship.relation_type).split(' ')[0].replace('bg-', 'bg-')}`}></div> {/* Simple colored strip fallback logic needs improvement or just explicit colors */}
              {/* Better approach: use border-l-4 */}
              <div className={`absolute left-0 top-0 bottom-0 w-1 ${getRelationTypeColorClass(relationship.relation_type).replace('text-', 'bg-').split(' ')[1] || 'bg-slate-400'}`}></div>

              <CardContent className="p-4 pl-6">
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${getRelationTypeColorClass(relationship.relation_type)}`}>
                    {getRelationTypeLabel(relationship.relation_type)}
                  </span>
                  {relationship.confidence && (
                    <span className="text-xs text-muted-foreground">{relationship.confidence}%</span>
                  )}
                </div>

                <div className="flex items-center gap-2 mb-2 font-medium text-card-foreground">
                  <span>{sourceTerm.source_term}</span>
                  <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  <span>{targetTerm.source_term}</span>
                </div>

                <div className="text-xs text-muted-foreground mb-3 flex items-center gap-2">
                  <span>{sourceTerm.translated_term}</span>
                  <ArrowRight className="h-3 w-3 text-muted-foreground/50" />
                  <span>{targetTerm.translated_term}</span>
                </div>

                {relationship.context && (
                  <div className="text-xs text-muted-foreground bg-muted p-2 rounded italic border border-border">
                    &quot;{relationship.context}&quot;
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-accent/10 pt-4">
          <div className="text-xs text-muted-foreground">
            Показано {paginatedRelationships.length} из {filteredRelationships.length} связей (Страница {currentPage} из {totalPages})
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-1 text-xs border border-accent/20 rounded hover:bg-accent/10 text-accent disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            >
              Назад
            </button>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-xs border border-accent/20 rounded hover:bg-accent/10 text-accent disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            >
              Вперед
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
