// @vitest-environment jsdom
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import GlossaryEditor from '../../components/GlossaryEditor';
import api from '@/services/apiClient';

// Mock the API client
vi.mock('@/services/apiClient', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock ResizeObserver for ResponsiveContainer
global.ResizeObserver = class ResizeObserver {
  observe() {
    // do nothing
  }
  unobserve() {
    // do nothing
  }
  disconnect() {
    // do nothing
  }
};

describe('GlossaryEditor', () => {
  const mockTerms = [
    {
      id: 1,
      source_term: 'Apple',
      translated_term: 'Яблоко',
      category: 'other',
      frequency: 10,
      status: 'approved',
      occurrences_data: [],
      centrality_score: 5,
    },
    {
      id: 2,
      source_term: 'Banana',
      translated_term: 'Банан',
      category: 'other',
      frequency: 5,
      status: 'pending',
      occurrences_data: [],
      centrality_score: 2,
    },
    {
      id: 3,
      source_term: 'Cherry',
      translated_term: 'Вишня',
      category: 'other',
      frequency: 20,
      status: 'pending',
      occurrences_data: [],
      centrality_score: 8,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue({ data: mockTerms });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders correctly and loads terms', async () => {
    render(<GlossaryEditor projectId={1} />);

    // Check loading state (might pass quickly)
    // await waitFor(() => expect(screen.getByRole('status')).toBeInTheDocument()); // Assuming Spinner has role status or similar, but let's just wait for data

    await waitFor(() => {
      expect(screen.getByText('Глоссарий (3)')).toBeInTheDocument();
    });

    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('Banana')).toBeInTheDocument();
    expect(screen.getByText('Cherry')).toBeInTheDocument();
  });

  it('sorts terms by frequency (default desc)', async () => {
    render(<GlossaryEditor projectId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Cherry')).toBeInTheDocument();
    });

    // Default sort is frequency desc
    // Order should be: Cherry (20), Apple (10), Banana (5)

    // We check the order of rows. First row is header.
    // We can get all rows in tbody
    const rows = screen.getAllByRole('row');
    // rows[0] is header
    expect(rows[1]).toHaveTextContent('Cherry');
    expect(rows[2]).toHaveTextContent('Apple');
    expect(rows[3]).toHaveTextContent('Banana');
  });

  it('sorts terms by frequency asc when toggled', async () => {
    render(<GlossaryEditor projectId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Cherry')).toBeInTheDocument();
    });

    // Click sort order button (default is desc, title="По убыванию")
    const sortBtn = screen.getByTitle('По убыванию');
    fireEvent.click(sortBtn);

    // Now should be asc: Banana (5), Apple (10), Cherry (20)
    await waitFor(() => {
       const rows = screen.getAllByRole('row');
       expect(rows[1]).toHaveTextContent('Banana');
       expect(rows[2]).toHaveTextContent('Apple');
       expect(rows[3]).toHaveTextContent('Cherry');
    });
  });

  it('filters/sorts by source_term', async () => {
      render(<GlossaryEditor projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Cherry')).toBeInTheDocument();
      });

      // Change sort to source_term
      const selects = screen.getAllByRole('combobox');
      // The sort select is the first one usually, or find by value
      const sortSelect = selects.find(s => s.value === 'frequency');
      // If it's controlled, value matches state.

      fireEvent.change(sortSelect, { target: { value: 'source_term' } });

      // Default order is still whatever it was last set to (desc by default in component state: const [sortOrder, setSortOrder] = useState('desc'))
      // Wait, initial state is 'desc'.
      // source_term desc: Cherry, Banana, Apple

      await waitFor(() => {
         const rows = screen.getAllByRole('row');
         expect(rows[1]).toHaveTextContent('Cherry');
         expect(rows[2]).toHaveTextContent('Banana');
         expect(rows[3]).toHaveTextContent('Apple');
      });

      // Toggle to asc
      const sortBtn = screen.getByTitle('По убыванию');
      fireEvent.click(sortBtn);

      // source_term asc: Apple, Banana, Cherry
      await waitFor(() => {
         const rows = screen.getAllByRole('row');
         expect(rows[1]).toHaveTextContent('Apple');
         expect(rows[2]).toHaveTextContent('Banana');
         expect(rows[3]).toHaveTextContent('Cherry');
      });
  });
});
