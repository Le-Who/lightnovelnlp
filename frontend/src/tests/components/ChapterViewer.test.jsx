// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ChapterViewer from "../../components/ChapterViewer";
import api from "@/services/apiClient";

// Mock the API client
vi.mock("@/services/apiClient", () => ({
  default: {
    get: vi.fn(),
  },
}));

// Mock createPortal to render children directly for testing
vi.mock("react-dom", async () => {
  const actual = await vi.importActual("react-dom");
  return {
    ...actual,
    createPortal: (node) => node,
  };
});

describe("ChapterViewer", () => {
  const mockChapters = [
    {
      id: 1,
      title: "Chapter 1",
      original_text_length: 100,
      translated_text_length: 100,
      order: 1,
    },
    {
      id: 2,
      title: "Chapter 2",
      original_text_length: 120,
      translated_text_length: 120,
      order: 2,
    },
    {
      id: 3,
      title: "Chapter 3",
      original_text_length: 140,
      translated_text_length: 140,
      order: 3,
    },
  ];

  const mockChapterDetail = {
    id: 2,
    title: "Chapter 2",
    original_text: "Original content of Chapter 2",
    translated_text: "Translated content of Chapter 2",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Default response for chapter list
    api.get.mockImplementation((url) => {
      if (url.includes("/projects/123/chapters")) {
        return Promise.resolve({ data: mockChapters });
      }
      return Promise.resolve({ data: {} });
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders chapter list correctly", async () => {
    render(<ChapterViewer projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText("Chapter 1")).toBeInTheDocument();
      expect(screen.getByText("Chapter 2")).toBeInTheDocument();
      expect(screen.getByText("Chapter 3")).toBeInTheDocument();
    });
  });

  it("opens reader mode on chapter click", async () => {
    render(<ChapterViewer projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText("Chapter 2")).toBeInTheDocument();
    });

    // Mock response for specific chapter
    api.get.mockImplementation((url) => {
      if (url === "/projects/chapters/2") {
        return Promise.resolve({ data: mockChapterDetail });
      }
      return Promise.resolve({ data: mockChapters }); // fallback
    });

    fireEvent.click(screen.getByText("Chapter 2"));

    await waitFor(() => {
      expect(screen.getByText("Active_File")).toBeInTheDocument();
      // "Chapter 2" text should be present in the reader header
      expect(screen.getAllByText("Chapter 2").length).toBeGreaterThan(0);
    });
  });

  it("navigates to previous/next chapter with buttons", async () => {
    render(<ChapterViewer projectId="123" />);

    // Wait for list
    await waitFor(() => screen.getByText("Chapter 2"));

    // Enter reader mode for Chapter 2
    api.get.mockImplementation((url) => {
      if (url === "/projects/chapters/2") {
        return Promise.resolve({ data: mockChapterDetail });
      }
      if (url === "/projects/chapters/1") {
        return Promise.resolve({
          data: { ...mockChapterDetail, id: 1, title: "Chapter 1" },
        });
      }
      if (url === "/projects/chapters/3") {
        return Promise.resolve({
          data: { ...mockChapterDetail, id: 3, title: "Chapter 3" },
        });
      }
      return Promise.resolve({ data: mockChapters });
    });

    fireEvent.click(screen.getByText("Chapter 2"));

    await waitFor(() => {
      expect(screen.getByText("Active_File")).toBeInTheDocument();
    });

    // Click Previous
    const prevButton = screen.getByRole("button", { name: /Previous Chapter/i });
    fireEvent.click(prevButton);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/projects/chapters/1");
    });
  });

  it("navigates with keyboard shortcuts", async () => {
    render(<ChapterViewer projectId="123" />);

    // Wait for list
    await waitFor(() => screen.getByText("Chapter 2"));

    // Setup mocks
    api.get.mockImplementation((url) => {
      if (url === "/projects/chapters/2") {
        return Promise.resolve({ data: mockChapterDetail });
      }
      if (url === "/projects/chapters/1") {
        return Promise.resolve({
          data: { ...mockChapterDetail, id: 1, title: "Chapter 1" },
        });
      }
      if (url === "/projects/chapters/2") { // Added explicitly for re-fetch
         return Promise.resolve({ data: mockChapterDetail });
      }
      if (url === "/projects/chapters/3") {
        return Promise.resolve({
          data: { ...mockChapterDetail, id: 3, title: "Chapter 3" },
        });
      }
      return Promise.resolve({ data: mockChapters });
    });

    // Enter reader mode for Chapter 2
    fireEvent.click(screen.getByText("Chapter 2"));

    await waitFor(() => {
      expect(screen.getByText("Active_File")).toBeInTheDocument();
    });

    // Press ArrowLeft
    fireEvent.keyDown(window, { key: "ArrowLeft" });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/projects/chapters/1");
    });

    // We can test ArrowRight by navigating back to 2 from 1
    // The component state should have updated to Chapter 1 after the previous waitFor resolved?
    // Note: handleSelectChapter sets selectedChapter.
    // So current selectedChapter is Chapter 1.
    // Index of Chapter 1 is 0.
    // ArrowRight from Chapter 1 should go to Chapter 2 (index 1).

    // Clear mocks to ensure we catch the new call
    api.get.mockClear();

    fireEvent.keyDown(window, { key: "ArrowRight" });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/projects/chapters/2");
    });
  });

  it("has accessible labels on navigation buttons", async () => {
    render(<ChapterViewer projectId="123" />);
    await waitFor(() => screen.getByText("Chapter 2"));

    // Mock and enter reader
    api.get.mockResolvedValue({ data: mockChapterDetail });
    fireEvent.click(screen.getByText("Chapter 2"));

    await waitFor(() => {
      expect(screen.getByText("Active_File")).toBeInTheDocument();
    });

    const prevButton = screen.getByRole("button", { name: /Previous Chapter/i });
    const nextButton = screen.getByRole("button", { name: /Next Chapter/i });

    expect(prevButton).toBeInTheDocument();
    expect(nextButton).toBeInTheDocument();
  });
});
