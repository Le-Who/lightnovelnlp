// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ChapterManager from "../../components/ChapterManager";
import api from "@/services/apiClient";

// Mock the API client
vi.mock("@/services/apiClient", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock window.confirm
const mockConfirm = vi.fn();
global.confirm = mockConfirm;

// Mock window.alert
const mockAlert = vi.fn();
global.alert = mockAlert;

describe("ChapterManager", () => {
  const mockChapters = [
    {
      id: 1,
      title: "Chapter 1",
      original_text: "Original text content",
      original_text_length: 21,
      translated_text: null,
      translated_text_length: 0,
      analysis_status: "pending",
      translation_status: "idle",
      order: 1,
    },
    {
      id: 2,
      title: "Chapter 2",
      original_text: "Another chapter content",
      original_text_length: 23,
      translated_text: "Translated text",
      translated_text_length: 15,
      analysis_status: "completed",
      translation_status: "completed",
      order: 2,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockConfirm.mockReturnValue(true); // Default confirm to true
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading state initially", async () => {
    // Mock API to return a promise that doesn't resolve immediately to simulate loading
    api.get.mockImplementation(() => new Promise(() => {}));

    render(<ChapterManager projectId="123" />);

    // Since loading renders skeletons, look for them or just test we don't crash
    expect(document.querySelector('.divide-y')).toBeInTheDocument();
  });

  it("renders chapters list correctly", async () => {
    api.get.mockResolvedValue({ data: mockChapters });

    render(<ChapterManager projectId="123" />);

    // Wait for text from mock to appear
    await waitFor(() => {
      expect(screen.getByText("Chapter 1")).toBeInTheDocument();
    });

    expect(screen.getByText("Chapter 2")).toBeInTheDocument();
    expect(screen.getByText("PENDING")).toBeInTheDocument(); // Status for Chapter 1
    expect(screen.getByText("READY")).toBeInTheDocument(); // Status for Chapter 2
  });

  it("renders empty state correctly", async () => {
    api.get.mockResolvedValue({ data: [] });

    render(<ChapterManager projectId="123" />);

    // Wait for empty state
    await waitFor(() => {
      expect(screen.getByText(/NO_FILES_FOUND/i)).toBeInTheDocument();
    });
  });

  it("handles API error on load", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    api.get.mockRejectedValue(new Error("Network error"));

    render(<ChapterManager projectId="123" />);

    await waitFor(() => {
      expect(
        screen.getByText(/CONNECTION_ERROR: FAILED_TO_FETCH_DATA/i),
      ).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it("creates a new chapter", async () => {
    // Initial load
    api.get.mockResolvedValueOnce({ data: [] });

    render(<ChapterManager projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText(/NO_FILES_FOUND/i)).toBeInTheDocument();
    });

    // Click NEW_FILE
    fireEvent.click(screen.getByText(/NEW_FILE/i));

    // Check if modal is open
    expect(screen.getByText(/NEW_CHAPTER_ENTRY/i)).toBeInTheDocument();

    // Fill inputs
    fireEvent.change(screen.getByLabelText(/Filename \/ Title/i), {
      target: { value: "New Chapter" },
    });
    fireEvent.change(screen.getByLabelText(/Content Data/i), {
      target: { value: "Some content" },
    });

    // Mock post response and subsequent get
    api.post.mockResolvedValueOnce({
      data: { id: 3, title: "New Chapter", original_text: "Some content" },
    });
    api.get.mockResolvedValueOnce({
      data: [
        {
          id: 3,
          title: "New Chapter",
          original_text: "Some content",
          analysis_status: "idle",
          translation_status: "idle",
        },
      ],
    });

    // Click EXECUTE_WRITE
    fireEvent.click(screen.getByText(/EXECUTE_WRITE/i));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/projects/123/chapters", {
        title: "New Chapter",
        original_text: "Some content",
      });
      expect(api.get).toHaveBeenCalledTimes(2); // Initial load + reload after create
      expect(screen.getByText("New Chapter")).toBeInTheDocument();
    });
  });

  it("deletes a chapter", async () => {
    // Initial load with one chapter
    api.get.mockResolvedValueOnce({ data: mockChapters.slice(0, 1) });

    render(<ChapterManager projectId="123" />);

    await waitFor(() =>
      expect(screen.getByText("Chapter 1")).toBeInTheDocument(),
    );

    // Mock delete response and subsequent get
    api.delete.mockResolvedValueOnce({});
    api.get.mockResolvedValueOnce({ data: [] });

    // Click PURGE (Trash icon)
    const deleteButton = screen.getByRole("button", { name: /PURGE/i });
    fireEvent.click(deleteButton);

    expect(mockConfirm).toHaveBeenCalledWith("CONFIRM_DELETION_SEQUENCE?");

    await waitFor(() => {
      expect(api.delete).toHaveBeenCalledWith("/projects/chapters/1");
      expect(api.get).toHaveBeenCalledTimes(2);
      expect(screen.queryByText("Chapter 1")).not.toBeInTheDocument();
    });
  });

  it("analyzes a chapter", async () => {
    // Initial load
    api.get.mockResolvedValueOnce({ data: mockChapters.slice(0, 1) });

    render(<ChapterManager projectId="123" />);

    await waitFor(() =>
      expect(screen.getByText("Chapter 1")).toBeInTheDocument(),
    );

    // Mock analyze response
    api.post.mockResolvedValueOnce({});

    // Click ANALYZE
    const analyzeButton = screen.getByRole("button", { name: /ANALYZE/i });
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        "/processing/chapters/1/analyze-async",
      );
    });
  });

  it("translates a chapter", async () => {
    // Initial load
    api.get.mockResolvedValueOnce({ data: mockChapters.slice(0, 1) });

    render(<ChapterManager projectId="123" />);

    await waitFor(() =>
      expect(screen.getByText("Chapter 1")).toBeInTheDocument(),
    );

    // Mock translate response
    api.post.mockResolvedValueOnce({});

    // Click TRANSLATE
    const translateButton = screen.getByRole("button", { name: /TRANSLATE/i });
    fireEvent.click(translateButton);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        "/translation/chapters/1/translate-async",
      );
    });
  });
});
