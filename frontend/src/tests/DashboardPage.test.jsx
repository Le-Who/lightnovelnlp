import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import DashboardPage from '../pages/DashboardPage'
import api from '../services/apiClient'

// Mock apiClient
vi.mock('../services/apiClient', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn()
  }
}))

describe('DashboardPage', () => {
  const mockProjects = [
    {
      id: 1,
      name: 'Project Alpha',
      genre: 'scifi',
      chapters_count: 5,
      created_at: new Date().toISOString()
    },
    {
      id: 2,
      name: 'Project Beta',
      genre: 'fantasy',
      chapters_count: 2,
      created_at: new Date().toISOString()
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockResolvedValue({ data: mockProjects })
  })

  it('renders project list', async () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      expect(screen.getByText('Project Beta')).toBeInTheDocument()
    })
  })

  // This test will fail initially because we haven't implemented the Link yet
  // But we want to ensure the structure is correct once implemented
  it('renders project name as a link', async () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      const link = screen.getByRole('link', { name: 'Project Alpha' })
      expect(link).toHaveAttribute('href', '/projects/1')
    })
  })

  it('renders delete button with aria-label', async () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      // Initially, it might only find by title or role button
      const deleteButton = screen.getByLabelText('Delete project Project Alpha')
      expect(deleteButton).toBeInTheDocument()
    })
  })
})
