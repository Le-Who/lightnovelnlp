import React from 'react'
import { Link } from 'react-router-dom'

export default function ProjectList({ projects }) {
  if (!projects?.length) return <div>Проекты отсутствуют</div>
  
  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {projects.map((p) => (
        <Link 
          key={p.id} 
          to={`/projects/${p.id}`}
          style={{ 
            textDecoration: 'none', 
            color: 'inherit',
            display: 'block',
            padding: 16,
            border: '1px solid #ddd',
            borderRadius: 8,
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = '#f5f5f5'
            e.target.style.transform = 'translateY(-2px)'
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = 'white'
            e.target.style.transform = 'translateY(0)'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: '0 0 4px 0' }}>{p.name}</h3>
              <small style={{ color: '#666' }}>
                Создан: {new Date(p.created_at).toLocaleDateString()}
              </small>
            </div>
            <div style={{ color: '#2196F3', fontSize: '0.9em' }}>
              Открыть →
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
