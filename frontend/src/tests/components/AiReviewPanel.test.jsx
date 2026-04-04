import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import { AiReviewPanel } from '../../components/themes/neon/AiReviewPanel';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';

describe('AiReviewPanel - Component Behavior Test (MSW)', () => {
  const chapterId = 42;

  it('renders loading state initially while fetching review', () => {
    // Arrange: response never resolves — no wall-clock cost
    server.use(
      http.get('*/api/v1/translation/chapters/:id/review', () => {
        return new Promise(() => {}); // intentionally never resolves
      })
    );

    // Act
    render(<AiReviewPanel chapterId={chapterId} />);

    // Assert — loading indicator visible while inflight
    expect(screen.getByText(/RUNNING_QA_DIAGNOSTICS/i)).toBeInTheDocument();
  });

  it('renders empty audit state when review is not yet available', async () => {
    // Arrange
    server.use(
      http.get('*/api/v1/translation/chapters/:id/review', () => {
        return HttpResponse.json({ review_available: false });
      })
    );

    // Act
    render(<AiReviewPanel chapterId={chapterId} />);

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/NO_AUDIT_DATA_AVAILABLE/i)).toBeInTheDocument();
      expect(screen.getByText(/RUN_AUDIT/i)).toBeInTheDocument();
    });
  });

  it('renders structured review data from valid AI JSON', async () => {
    // Act — uses default happy-path handler from handlers.js
    render(<AiReviewPanel chapterId={chapterId} />);

    // Assert
    await waitFor(() => {
      expect(screen.getByText('8/10')).toBeInTheDocument();
      expect(screen.getByText(/PASSED/i)).toBeInTheDocument();
      expect(screen.getByText(/GLOSSARY_VIOLATIONS/i)).toBeInTheDocument();
      expect(screen.getByText(/Use formal tone/i)).toBeInTheDocument();
    });
  });

  it('falls back to raw text when review_text is not valid JSON', async () => {
    // Arrange
    const rawMalformattedText = '```json { badly: formatted] ```';
    server.use(
      http.get('*/api/v1/translation/chapters/:id/review', () => {
        return HttpResponse.json({ review_available: true, review_text: rawMalformattedText });
      })
    );

    // Act
    render(<AiReviewPanel chapterId={chapterId} />);

    // Assert — component must not throw; renders raw string as fallback
    await waitFor(() => {
      expect(screen.getByText(rawMalformattedText)).toBeInTheDocument();
    });
  });

  it('invokes correction API when FORCE_AI_CORRECTION is clicked', async () => {
    // Arrange
    let correctionTriggered = false;
    server.use(
      http.get('*/api/v1/translation/chapters/:id/review', () => {
        return HttpResponse.json({
          review_available: true,
          review_text: JSON.stringify({
            score: 8,
            passed: false,
            violations: [{ term: 'Aura', expected: 'Qi', found: 'Aura', context: 'Using Aura instead of Qi' }],
            style_notes: [],
          }),
        });
      }),
      http.post('*/api/v1/translation/chapters/:id/translate-with-review', () => {
        correctionTriggered = true;
        return HttpResponse.json({ status: 'started' });
      })
    );

    const onCorrectionStartedMock = vi.fn();
    render(<AiReviewPanel chapterId={chapterId} onCorrectionStarted={onCorrectionStartedMock} />);

    // Act — wait for button then click
    const forceBtn = await screen.findByRole('button', { name: /FORCE_AI_CORRECTION/i });
    fireEvent.click(forceBtn);

    // Assert
    await waitFor(() => {
      expect(correctionTriggered).toBe(true);
      expect(onCorrectionStartedMock).toHaveBeenCalled();
    });
  });
});
