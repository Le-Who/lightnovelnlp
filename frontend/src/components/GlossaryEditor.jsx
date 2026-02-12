import React, { useState, useEffect, useMemo } from 'react'
import api from '../services/apiClient'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from './ui/Table'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { Badge } from './ui/Badge'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Spinner } from './ui/Spinner'
import { X, Edit2, Check, Trash2, ArrowUpDown } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { Label } from './ui/Label'
import { Textarea } from './ui/Textarea'

export default function GlossaryEditor({ projectId }) {
  const [terms, setTerms] = useState([])
  const [loading, setLoading] = useState(false)
  const [editingTerm, setEditingTerm] = useState(null) // Term being edited in Modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)

  // Sorting state
  const [sortBy, setSortBy] = useState('frequency') // Default to frequency as it's often most relevant
  const [sortOrder, setSortOrder] = useState('desc') // Default desc for frequency

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

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') setIsEditModalOpen(false)
    }

    if (isEditModalOpen) {
      document.addEventListener('keydown', handleEsc)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = ''
    }
  }, [isEditModalOpen])

  // Client-side sorting logic
  const sortedTerms = useMemo(() => {
    return [...terms].sort((a, b) => {
      let valA = a[sortBy]
      let valB = b[sortBy]

      // Handle specifics
      if (sortBy === 'source_term' || sortBy === 'translated_term') {
        valA = (valA || '').toLowerCase()
        valB = (valB || '').toLowerCase()
        return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA)
      }

      if (sortBy === 'category') {
        valA = a.category || ''
        valB = b.category || ''
        return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA)
      }

      if (sortBy === 'status') {
        valA = a.status || ''
        valB = b.status || ''
        return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA)
      }

      // Default string/number comparison
      if (valA === null || valA === undefined) valA = ''
      if (valB === null || valB === undefined) valB = ''

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1
      return 0
    })
  }, [terms, sortBy, sortOrder])

  const approveTerm = async (termId) => {
    try {
      await api.post(`/glossary/terms/${termId}/approve`)
      loadTerms()
    } catch (e) {
      console.error('Error approving term:', e)
      alert('Ошибка утверждения термина')
    }
  }

  const updateTerm = async () => {
    if (!editingTerm) return
    try {
      await api.put(`/glossary/terms/${editingTerm.id}`, {
        translated_term: editingTerm.translated_term,
        context: editingTerm.context
      })
      setIsEditModalOpen(false)
      setEditingTerm(null)
      loadTerms()
    } catch (e) {
      console.error('Error updating term:', e)
      alert('Ошибка обновления термина')
    }
  }

  const openEditModal = (term) => {
    setEditingTerm({ ...term })
    setIsEditModalOpen(true)
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

  const getStatusBadge = (status) => {
    if (status === 'approved') return <Badge variant="success" className="bg-green-500/10 text-green-500 border-green-500/20">Approved</Badge>
    return <Badge variant="warning" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">Pending</Badge>
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

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 50

  // Calculate pagination
  const totalPages = Math.ceil(sortedTerms.length / itemsPerPage)

  const paginatedTerms = useMemo(() => {
    return sortedTerms.slice(
      (currentPage - 1) * itemsPerPage,
      currentPage * itemsPerPage
    )
  }, [sortedTerms, currentPage, itemsPerPage])

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage)
      // Scroll to top of table
      document.querySelector('.glossary-table-container')?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  if (loading && terms.length === 0) return <div className="flex justify-center p-8"><Spinner /></div>

  return (
    <Card className="overflow-hidden border-accent/20 glossary-table-container">
      <CardHeader>
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <CardTitle>Глоссарий ({terms.length})</CardTitle>

          <div className="flex gap-2 items-center text-sm">
            <span className="text-muted-foreground">Сортировка:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground"
              aria-label="Сортировать по"
            >
              <option value="frequency">Частота</option>
              <option value="source_term">Оригинал (А-Я)</option>
              <option value="translated_term">Перевод (А-Я)</option>
              <option value="category">Категория</option>
              <option value="status">Статус</option>
              <option value="id">ID</option>
            </select>

            <button
              onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
              className="h-9 w-9 flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent/10 hover:text-accent transition-colors"
              title={sortOrder === 'asc' ? "По возрастанию" : "По убыванию"}
              aria-label={sortOrder === 'asc' ? "По возрастанию" : "По убыванию"}
            >
              <ArrowUpDown className="h-4 w-4" />
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {terms.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            Термины отсутствуют. Запустите анализ главы для извлечения терминов.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-md border border-accent/10">
              <div className="w-full">
                <Table className="table-fixed w-full">
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-accent/10">
                      <TableHead className="w-[20%] text-center">Оригинал</TableHead>
                      <TableHead className="w-[20%] text-center">Перевод</TableHead>
                      <TableHead className="w-[12%] hidden md:table-cell text-center">Категория</TableHead>
                      <TableHead className="w-[8%] text-center">Частота</TableHead>
                      <TableHead className="w-[10%] hidden lg:table-cell text-center">Плотность</TableHead>
                      <TableHead className="w-[10%] hidden md:table-cell text-center">Центр.</TableHead>
                      <TableHead className="w-[6%] hidden md:table-cell text-center text-[10px] uppercase">Первое уп.</TableHead>
                      <TableHead className="w-[6%] hidden md:table-cell text-center text-[10px] uppercase">Посл. уп.</TableHead>
                      <TableHead className="w-[8%] text-center">Статус</TableHead>
                      <TableHead className="w-[8%] text-right">Действия</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedTerms.map((term) => (
                      <TableRow key={term.id} className="hover:bg-accent/5 transition-colors border-accent/5">
                        {/* Source Term - Wraps text */}
                        <TableCell className="font-medium text-card-foreground align-top p-3 break-words whitespace-normal leading-tight">
                          {term.source_term}
                          {term.context && (
                            <div className="text-xs text-muted-foreground mt-1 italic whitespace-normal leading-tight opacity-70">
                              {term.context}
                            </div>
                          )}
                        </TableCell>

                        {/* Translated Term - Wraps text */}
                        <TableCell className="text-card-foreground align-top p-3 break-words whitespace-normal leading-tight">
                          {term.translated_term || <span className="text-muted-foreground/40 italic">Не переведено</span>}
                        </TableCell>

                        <TableCell className="text-card-foreground hidden md:table-cell align-top text-center p-3">
                          <span className="inline-flex px-2 py-0.5 rounded text-xs bg-secondary/20 text-secondary-foreground border border-secondary/30">
                            {getCategoryLabel(term.category)}
                          </span>
                        </TableCell>

                        <TableCell className="text-card-foreground align-top text-center p-3 font-mono">{term.frequency || 1}</TableCell>

                        <TableCell className="h-full p-1 hidden lg:table-cell align-top">
                          {term.occurrences_data && term.occurrences_data.length > 0 ? (
                            <div className="h-10 w-full">
                              <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={term.occurrences_data}>
                                  <Line type="monotone" dataKey="freq" stroke="#8884d8" strokeWidth={2} dot={false} />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          ) : (
                            <span className="text-xs text-muted-foreground">-</span>
                          )}
                        </TableCell>

                        <TableCell className="hidden md:table-cell align-top text-center p-3">
                          <Badge variant={term.centrality_score > 0 ? "default" : "secondary"} className="text-[10px]">
                            {term.centrality_score ? term.centrality_score.toFixed(2) : '0.00'}
                          </Badge>
                        </TableCell>

                        <TableCell className="text-card-foreground hidden md:table-cell align-top text-center p-3 text-xs text-muted-foreground">
                          {term.first_chapter_order || '-'}
                        </TableCell>

                        <TableCell className="text-card-foreground hidden md:table-cell align-top text-center p-3 text-xs text-muted-foreground">
                          {term.last_chapter_order || '-'}
                        </TableCell>

                        <TableCell className="align-top text-center p-3">{getStatusBadge(term.status)}</TableCell>

                        <TableCell className="text-right align-top p-3">
                          <div className="flex justify-end gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-8 w-8 p-0 hover:text-accent hover:bg-accent/10"
                              onClick={() => openEditModal(term)}
                              title="Редактировать"
                              aria-label={`Редактировать термин: ${term.source_term}`}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>

                            {term.status !== 'approved' && (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-8 w-8 p-0 hover:text-green-500 hover:bg-green-500/10"
                                onClick={() => approveTerm(term.id)}
                                title="Утвердить"
                                aria-label={`Утвердить термин: ${term.source_term}`}
                              >
                                <Check className="h-4 w-4" />
                              </Button>
                            )}

                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-8 w-8 p-0 hover:text-destructive hover:bg-destructive/10"
                              onClick={() => deleteTerm(term.id)}
                              title="Удалить"
                              aria-label={`Удалить термин: ${term.source_term}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t border-accent/10 pt-4">
                <div className="text-xs text-muted-foreground">
                  Показано {paginatedTerms.length} из {sortedTerms.length} терминов (Страница {currentPage} из {totalPages})
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="h-8 text-xs hover:border-accent hover:text-accent"
                  >
                    Назад
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="h-8 text-xs hover:border-accent hover:text-accent"
                  >
                    Вперед
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>

      {/* Edit Term Modal */}
      {isEditModalOpen && editingTerm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-term-title"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsEditModalOpen(false)
          }}
        >
          <div className="w-full max-w-lg border border-accent bg-surface/95 relative shadow-[0_0_50px_rgba(0,243,255,0.2)]">
            <div className="flex items-center justify-between p-4 border-b border-accent/20 bg-accent/5">
              <h3 id="edit-term-title" className="text-accent font-bold uppercase tracking-widest flex items-center">
                <Edit2 className="w-4 h-4 mr-2" /> Редактирование термина
              </h3>
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="text-text-muted hover:text-destructive transition-colors"
                aria-label="Закрыть"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <Label className="text-[10px] uppercase text-accent tracking-widest mb-1 block">Оригинал</Label>
                <div className="p-2 bg-accent/5 border border-accent/10 text-text font-bold rounded">
                  {editingTerm.source_term}
                </div>
              </div>

              <div>
                <Label htmlFor="edit-trans" className="text-[10px] uppercase text-accent tracking-widest mb-1 block">Перевод</Label>
                <Input
                  id="edit-trans"
                  value={editingTerm.translated_term}
                  onChange={(e) => setEditingTerm(prev => ({ ...prev, translated_term: e.target.value }))}
                  className="bg-bg/50 border-accent/30 text-text font-bold"
                  autoFocus
                />
              </div>

              <div>
                <Label htmlFor="edit-context" className="text-[10px] uppercase text-accent tracking-widest mb-1 block">Контекст / Заметки</Label>
                <Textarea
                  id="edit-context"
                  value={editingTerm.context || ''}
                  onChange={(e) => setEditingTerm(prev => ({ ...prev, context: e.target.value }))}
                  className="bg-bg/50 border-accent/30 text-text min-h-[100px] resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-accent/10 mt-4">
                <Button
                  variant="ghost"
                  onClick={() => setIsEditModalOpen(false)}
                  className="text-muted-foreground hover:text-text uppercase tracking-wider"
                >
                  Отмена
                </Button>
                <Button
                  onClick={updateTerm}
                  className="bg-accent text-bg hover:bg-secondary-accent font-bold uppercase tracking-wider min-w-[120px]"
                >
                  Сохранить
                </Button>
              </div>
            </div>

            {/* Corner Accents */}
            <div className="absolute top-0 left-0 w-2 h-2 bg-accent" />
            <div className="absolute top-0 right-0 w-2 h-2 bg-accent" />
            <div className="absolute bottom-0 left-0 w-2 h-2 bg-accent" />
            <div className="absolute bottom-0 right-0 w-2 h-2 bg-accent" />
          </div>
        </div>
      )}
    </Card>
  )
}
