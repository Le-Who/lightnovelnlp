import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { NeonProjectPage } from '@/components/themes/neon/NeonProjectPage'

vi.mock('@/services/apiClient', () => ({
  default: {
    put: vi.fn(),
  }
}))

// Mock child components to avoid deep rendering
vi.mock('@/components/ChapterManager.jsx', () => ({ default: () => <div data-testid="chapter-manager">Chapter Manager</div> }))
vi.mock('@/components/ChapterViewer.jsx', () => ({ default: () => <div data-testid="chapter-viewer">Chapter Viewer</div> }))
vi.mock('@/components/GlossaryEditor.jsx', () => ({ default: () => <div data-testid="glossary-editor">Glossary Editor</div> }))
vi.mock('@/components/RelationshipsViewer.jsx', () => ({ default: () => <div data-testid="relationships-viewer">Relationships Viewer</div> }))
vi.mock('@/components/BatchProcessor.jsx', () => ({ default: () => <div data-testid="batch-processor">Batch Processor</div> }))
vi.mock('@/components/GlossaryVersionManager.jsx', () => ({ default: () => <div data-testid="glossary-version-manager">Glossary Version Manager</div> }))

describe('NeonProjectPage', () => {
  const mockProject = {
    id: 1,
    name: 'Test Project',
    genre: 'xianxia'
  }

  it('renders loading state', () => {
    render(
      <BrowserRouter>
        <NeonProjectPage project={null} loading={true} projectId="1" onRefresh={() => {}} />
      </BrowserRouter>
    )
    expect(screen.getByText(/ESTABLISHING_UPLINK/i)).toBeInTheDocument()
  })

  it('renders error state when project is null and not loading', () => {
    render(
      <BrowserRouter>
        <NeonProjectPage project={null} loading={false} projectId="1" onRefresh={() => {}} />
      </BrowserRouter>
    )
    expect(screen.getByText(/ERROR: NULL_TARGGET_DATA/i)).toBeInTheDocument()
  })

  it('renders project content', () => {
    render(
      <BrowserRouter>
        <NeonProjectPage project={mockProject} loading={false} projectId="1" onRefresh={() => {}} />
      </BrowserRouter>
    )
    expect(screen.getByText('Test Project')).toBeInTheDocument()
    // Check for default tab (Chapter Manager)
    expect(screen.getByTestId('chapter-manager')).toBeInTheDocument()
  })
})
