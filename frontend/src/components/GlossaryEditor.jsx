import React, { useState, useEffect } from 'react'
import api from '../services/apiClient'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from './ui/Table'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { Badge } from './ui/Badge'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Spinner } from './ui/Spinner'
import { Save, X, Edit2, Check, Trash2 } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'

export default function GlossaryEditor({ projectId }) {
  const [terms, setTerms] = useState([])
  const [loading, setLoading] = useState(false)
  const [editingTerm, setEditingTerm] = useState(null)
  const [sortBy, setSortBy] = useState('id')
  const [sortOrder, setSortOrder] = useState('asc')

  const loadTerms = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/glossary/${projectId}/terms`)

      // Frontend sorting to ensure it works regardless of backend implementation
      const sortedTerms = [...res.data].sort((a, b) => {
        let valA = a[sortBy]
        let valB = b[sortBy]

        // Handle nulls
        if (valA === null || valA === undefined) valA = ''
        if (valB === null || valB === undefined) valB = ''

        // String comparison for text fields
        if (typeof valA === 'string') {
          return sortOrder === 'asc'
            ? valA.localeCompare(valB)
            : valB.localeCompare(valA)
        }

        // Number comparison
        return sortOrder === 'asc' ? valA - valB : valB - valA
      })

      setTerms(sortedTerms)
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
  }, [projectId, sortBy, sortOrder])

  const approveTerm = async (termId) => {
    try {
      await api.post(`/glossary/terms/${termId}/approve`)
      loadTerms()
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

  const getStatusBadge = (status) => {
    if (status === 'approved') return <Badge variant="success">Утвержден</Badge>
    return <Badge variant="warning">Ожидает</Badge>
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

  if (loading && terms.length === 0) return <div className="flex justify-center p-8"><Spinner /></div>

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <CardTitle>Глоссарий</CardTitle>

          <div className="flex gap-2 items-center text-sm">
            <span className="text-muted-foreground">Сортировка:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground"
            >
              <option value="id">ID</option>
              {/* ... options ... */}
              <option value="created_at">Дата создания</option>
            </select>
            {/* ... order select ... */}
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground"
            >
              <option value="asc">По возр.</option>
              <option value="desc">По убыв.</option>
            </select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {terms.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            Термины отсутствуют. Запустите анализ главы для извлечения терминов.
          </div>
        ) : (
          <div className="rounded-md border overflow-x-auto"> {/* Added overflow-x-auto */}
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Оригинал</TableHead>
                  <TableHead>Перевод</TableHead>
                  <TableHead className="hidden md:table-cell">Категория</TableHead>
                  <TableHead>Частота</TableHead>
                  <TableHead className="w-[100px] hidden lg:table-cell">Плотность</TableHead>
                  <TableHead className="hidden lg:table-cell">Центральность</TableHead>
                  <TableHead>Первое появление</TableHead>
                  <TableHead className="hidden md:table-cell">Последнее появление</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {terms.map((term) => (
                  <TableRow key={term.id} className="hover:bg-accent/5"> {/* Neon friendly hover */}
                    <TableCell className="font-medium text-card-foreground">
                      {term.source_term}
                      {term.context && (
                        <div className="text-xs text-muted-foreground mt-1 italic whitespace-normal">
                          {term.context}
                        </div>
                      )}
                    </TableCell>
                    {/* ... Translation Cell ... */}
                    <TableCell className="text-card-foreground">
                      {editingTerm?.id === term.id ? (
                        <div className="flex items-center gap-2">
                          <Input
                            value={editingTerm.translated_term}
                            onChange={(e) => setEditingTerm({
                              ...editingTerm,
                              translated_term: e.target.value
                            })}
                            className="h-8 w-40"
                          />
                        </div>
                      ) : (
                        term.translated_term
                      )}
                    </TableCell>
                    <TableCell className="text-card-foreground hidden md:table-cell">{getCategoryLabel(term.category)}</TableCell>
                    <TableCell className="text-card-foreground">{term.frequency || 1}</TableCell>
                    <TableCell className="h-12 w-[100px] p-0 hidden lg:table-cell">
                      {term.occurrences_data && term.occurrences_data.length > 0 ? (
                        <div className="h-full w-full py-1">
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
                    <TableCell className="hidden lg:table-cell">
                      <Badge variant={term.centrality_score > 0 ? "default" : "secondary"}>
                        {term.centrality_score || 0}
                      </Badge>
                    </TableCell>
                    {/* Updated Badges for visibility */}
                    <TableCell className="text-card-foreground">
                      {term.first_chapter_order ? <span className="inline-flex items-center rounded-md border border-input bg-background px-2 py-0.5 text-xs font-medium text-foreground ring-1 ring-inset ring-ring/10 font-mono">Ch. {term.first_chapter_order}</span> : '-'}
                    </TableCell>
                    <TableCell className="text-card-foreground hidden md:table-cell">
                      {term.last_chapter_order ? <span className="inline-flex items-center rounded-md border border-input bg-background px-2 py-0.5 text-xs font-medium text-foreground ring-1 ring-inset ring-ring/10 font-mono">Ch. {term.last_chapter_order}</span> : '-'}
                    </TableCell>
                    <TableCell>{getStatusBadge(term.status)}</TableCell>
                    <TableCell className="text-right">
                      {/* Actions ... */}
                      <div className="flex justify-end gap-2">
                        {editingTerm?.id === term.id ? (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => updateTerm(term.id, {
                                translated_term: editingTerm.translated_term
                              })}
                            >
                              <Save className="h-4 w-4 text-green-600" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setEditingTerm(null)}
                            >
                              <X className="h-4 w-4 text-muted-foreground" />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setEditingTerm(term)}
                            >
                              <Edit2 className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                            </Button>
                            {term.status === 'pending' && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => approveTerm(term.id)}
                              >
                                <Check className="h-4 w-4 text-green-600" />
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => deleteTerm(term.id)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
