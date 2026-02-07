import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import ChapterManager from '@/components/ChapterManager'
import api from '@/services/apiClient'

// Mock the API client
vi.mock('@/services/apiClient', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  }
}))

// Mock ResizeObserver which is used by Recharts or other UI libs sometimes,
// though mostly for layout. Just in case.
global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
}))

describe('ChapterManager', () => {
  const projectId = 'test-project-id'

  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockResolvedValue({ data: [] })
  })

  it('opens create modal when NEW_FILE is clicked', async () => {
    render(<ChapterManager projectId={projectId} />)

    const newFileBtn = screen.getByText(/NEW_FILE/i)
    fireEvent.click(newFileBtn)

    await waitFor(() => {
      expect(screen.getByRole('dialog', { name: /NEW_CHAPTER_ENTRY/i })).toBeInTheDocument()
    })
  })

  it('shows loading state and calls API when creating a chapter', async () => {
    // Setup API mock response with delay to verify loading state
    api.post.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ data: {} }), 100)))

    render(<ChapterManager projectId={projectId} />)

    // Open modal
    fireEvent.click(screen.getByText(/NEW_FILE/i))

    // Fill form
    const titleInput = screen.getByLabelText(/Filename \/ Title/i)
    const contentInput = screen.getByLabelText(/Content Data/i)

    fireEvent.change(titleInput, { target: { value: 'Chapter 1' } })
    fireEvent.change(contentInput, { target: { value: 'Content...' } })

    // Click submit
    const submitBtn = screen.getByText(/EXECUTE_WRITE/i)
    fireEvent.click(submitBtn)

    // Check loading state
    expect(screen.getByText(/EXECUTING.../i)).toBeInTheDocument()
    expect(submitBtn).toBeDisabled()
    expect(titleInput).toBeDisabled()
    expect(contentInput).toBeDisabled()

    // Wait for completion
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(`/projects/${projectId}/chapters`, {
        title: 'Chapter 1',
        original_text: 'Content...'
      })
    })

    // Modal should be closed
    await waitFor(() => {
        expect(screen.queryByRole('dialog', { name: /NEW_CHAPTER_ENTRY/i })).not.toBeInTheDocument()
    })
  })
})
