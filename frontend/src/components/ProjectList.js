import React from 'react'

export default function ProjectList({ projects }) {
  if (!projects?.length) return <div>Проекты отсутствуют</div>
  return (
    <ul>
      {projects.map((p) => (
        <li key={p.id}>
          <strong>{p.name}</strong> <small>#{p.id}</small>
        </li>
      ))}
    </ul>
  )
}
