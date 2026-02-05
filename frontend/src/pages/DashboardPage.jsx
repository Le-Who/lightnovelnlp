import React, { useEffect, useState } from 'react'
import api from '../services/apiClient'
import ProjectList from '../components/ProjectList.jsx'

export default function DashboardPage() {
  const [projects, setProjects] = useState([])
  const [name, setName] = useState('')
  const [genre, setGenre] = useState('')
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.get('/projects/')
      setProjects(Array.isArray(res.data) ? res.data : [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const createProject = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    try {
      await api.post('/projects/', { name, genre: genre || 'other' })
      setName('')
      setGenre('')
      load()
    } catch (e) {
      console.error(e)
      alert('Ошибка создания проекта')
    }
  }

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>Проекты</h1>
      <form onSubmit={createProject} style={{ display: 'grid', gap: 10, maxWidth: 500, marginBottom: 30, padding: 20, border: '1px solid #ddd', borderRadius: 8 }}>
        <h3>Создать новый проект</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <label style={{ fontSize: '0.9em', fontWeight: 'bold' }}>Название:</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Например: Overlord"
            style={{ padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <label style={{ fontSize: '0.9em', fontWeight: 'bold' }}>Жанр:</label>
          <input
            list="genreOptions"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            placeholder="Выберите или введите свой жанр..."
            style={{ padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
          />
          <datalist id="genreOptions">
            <option value="fantasy">Фантастика</option>
            <option value="scifi">Научная фантастика</option>
            <option value="romance">Романтика</option>
            <option value="action">Боевик</option>
            <option value="mystery">Детектив/Мистерия</option>
            <option value="horror">Ужасы</option>
            <option value="slice_of_life">Повседневность</option>
            <option value="adventure">Приключения</option>
            <option value="wuxia">Wuxia (Китайское боевое фэнтези)</option>
            <option value="xianxia">Xianxia (Культивация бессмертия)</option>
            <option value="litrpg">LitRPG (Игровые механики)</option>
            <option value="isekai">Isekai (Попаданцы)</option>
            <option value="other">Другое</option>
          </datalist>
        </div>

        <button type="submit" style={{ padding: '10px', background: '#2196F3', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer', marginTop: 10 }}>
          Создать проект
        </button>
      </form>

      {loading ? <div>Загрузка…</div> : <ProjectList projects={projects} />}
    </div>
  )
}
