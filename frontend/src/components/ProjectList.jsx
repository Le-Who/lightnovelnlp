import React from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './ui/Card'
import { Badge } from './ui/Badge'
import { ArrowRight, BookOpen } from 'lucide-react'

export default function ProjectList({ projects }) {
  if (!Array.isArray(projects) || !projects.length) {
    return (
      <div className="text-center py-12 text-muted-foreground border border-dashed rounded-lg">
        Проекты отсутствуют. Создайте свой первый проект!
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {projects.map((p) => (
        <Link key={p.id} to={`/projects/${p.id}`} className="group">
          <Card className="h-full transition-all hover:shadow-md hover:border-primary group-hover:-translate-y-1">
            <CardHeader>
              <div className="flex justify-between items-start gap-4">
                <CardTitle className="text-lg line-clamp-2" title={p.name}>
                  {p.name}
                </CardTitle>
                <BookOpen className="h-5 w-5 text-muted-foreground shrink-0" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-2">
                <Badge variant="secondary" className="capitalize">
                  {p.genre || 'Другое'}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                Создан: {new Date(p.created_at).toLocaleDateString()}
              </p>
            </CardContent>
            <CardFooter>
              <div className="text-sm font-medium text-foreground flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                Открыть проект <ArrowRight className="h-4 w-4" />
              </div>
            </CardFooter>
          </Card>
        </Link>
      ))}
    </div>
  )
}
