import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import DashboardPage from '../pages/DashboardPage';
import { server } from './mocks/server';
import { http, HttpResponse } from 'msw';

describe('DashboardPage - UI Component Tests (MSW)', () => {

  // MSW handlers reset is done in setup.js, but we can override locally if needed

  it('renders a list of available projects sequentially', async () => {
    // Relying on default happy path in handlers.js
    render(
      <BrowserRouter>
         <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
       expect(screen.getByText('Project Alpha')).toBeInTheDocument();
       expect(screen.getByText('Project Beta')).toBeInTheDocument();
    });
  });

  it('creates a new project', async () => {
    let internalProjects = [
      { id: 1, name: 'Project Alpha' }
    ];
    let postBody = {};

    server.use(
      http.post('*/api/v1/projects/', async ({ request }) => {
        postBody = await request.json();
        const newProj = {
          id: 3,
          name: postBody.name,
          genre: postBody.genre,
          chapters_count: 0
        };
        internalProjects.push(newProj);
        return HttpResponse.json(newProj);
      }),
      http.get('*/api/v1/projects/', () => {
        return HttpResponse.json(internalProjects);
      })
    );

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    const nameInput = await screen.findByPlaceholderText(/ENTER_DESIGNATION/i);
    const genreInput = await screen.findByPlaceholderText(/SELECT_PROTOCOL/i);
    const submitBtn = screen.getByRole('button', { name: /EXECUTE/i });

    // Explicitly update input states
    fireEvent.change(nameInput, { target: { value: 'New Test Project' } });
    fireEvent.change(genreInput, { target: { value: 'system' } });
    
    // Check if state updated (value reflects)
    expect(nameInput.value).toBe('New Test Project');

    // Click submit and also trigger submit explicitly just in case
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(postBody.name).toBe('New Test Project');
      expect(screen.getByText('New Test Project')).toBeInTheDocument();
    });
  });

  it('deletes a selected project when confirmation clicked', async () => {
    let deletedIds = [];
    server.use(
      http.delete('*/api/v1/projects/:id', ({ params }) => {
        deletedIds.push(params.id);
        return new HttpResponse(null, { status: 204 });
      })
    );
    
    render(
      <BrowserRouter>
         <DashboardPage />
      </BrowserRouter>
    );

    const deleteBtn = await screen.findByLabelText('Delete project Project Alpha');
    
    const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => true);

    fireEvent.click(deleteBtn);

    await waitFor(() => {
       expect(deletedIds).toContain('1');
    });
    
    confirmSpy.mockRestore();
  });
});
