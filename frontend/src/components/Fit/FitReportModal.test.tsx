import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FitReportModal } from "./FitReportModal";
import * as useFitReportModule from "../../hooks/useFitReport";
import type { FitReport, SampleJobDescription } from "../../lib/types";

vi.mock("../../hooks/useFitReport");

const mockReport: FitReport = {
  role_title: "Full-Stack AI Engineer",
  jd_hash: "a".repeat(64),
  score: {
    overall_fit: "Strong Match",
    must_have_strong: 3,
    must_have_partial: 0,
    must_have_gap: 0,
    must_have_total: 3,
    nice_to_have_strong: 1,
    nice_to_have_partial: 0,
    nice_to_have_gap: 0,
    nice_to_have_total: 1,
    total_requirements: 4,
    headline: "Verified match across all core criteria.",
  },
  summary: "Comprehensive experience demonstrated.",
  requirements: [],
};

const mockPresets: SampleJobDescription[] = [
  {
    id: "sample-1",
    title: "Full-Stack AI Engineer (Strong Match)",
    company: "AI Labs",
    match_expectation: "strong",
    text: "We are seeking a Full-Stack AI Engineer with 3+ years of experience in FastAPI, Python, React, and Groq API pipelines.",
  },
];

describe("<FitReportModal />", () => {
  const defaultHookState = {
    status: "idle" as const,
    progress: null,
    report: null,
    error: null,
    presets: mockPresets,
    isLoadingPresets: false,
    activePreset: null,
    loadPreset: vi.fn(),
    submit: vi.fn(),
    abort: vi.fn(),
    reset: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useFitReportModule.useFitReport).mockReturnValue({
      ...defaultHookState,
    });
  });

  it("exposes unknown usage for a failed request with no final provider receipt", () => {
    vi.mocked(useFitReportModule.useFitReport).mockReturnValue({
      ...defaultHookState, status: "error", error: "Provider failed", errorReceipt: {},
    });
    render(<FitReportModal isOpen onClose={vi.fn()} onAskGap={vi.fn()} />);
    expect(screen.getByText(/Unknown \/ incomplete — receipt unavailable/)).toBeInTheDocument();
    expect(screen.getByText("Under the hood").closest("details")).not.toHaveAttribute("open");
  });

  it("does not render when isOpen is false", () => {
    const { container } = render(
      <FitReportModal isOpen={false} onClose={vi.fn()} onAskGap={vi.fn()} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("renders modal dialog, title, presets, textarea, and action buttons when open", () => {
    render(
      <FitReportModal isOpen={true} onClose={vi.fn()} onAskGap={vi.fn()} />
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Job Description Fit Report")).toBeInTheDocument();
    expect(screen.getByText("Full-Stack AI Engineer")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Paste complete job requirements/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Analyze Alignment/i })).toBeDisabled();
  });

  it("loads preset into state and calls loadPreset on click", () => {
    const loadPresetMock = vi.fn();
    vi.mocked(useFitReportModule.useFitReport).mockReturnValue({
      ...defaultHookState,
      loadPreset: loadPresetMock,
    });

    render(
      <FitReportModal isOpen={true} onClose={vi.fn()} onAskGap={vi.fn()} />
    );

    const presetBtn = screen.getByText("Full-Stack AI Engineer");
    fireEvent.click(presetBtn);

    expect(loadPresetMock).toHaveBeenCalledWith(mockPresets[0]);
  });

  it("calls submit when custom form is submitted", () => {
    const submitMock = vi.fn();
    vi.mocked(useFitReportModule.useFitReport).mockReturnValue({
      ...defaultHookState,
      submit: submitMock,
    });

    render(
      <FitReportModal isOpen={true} onClose={vi.fn()} onAskGap={vi.fn()} />
    );

    const textarea = screen.getByPlaceholderText(/Paste complete job requirements/i);
    fireEvent.change(textarea, {
      target: {
        value: "We are seeking a Full-Stack AI Engineer with 3+ years of experience in FastAPI and React.",
      },
    });

    const submitBtn = screen.getByRole("button", { name: /Analyze Alignment/i });
    fireEvent.click(submitBtn);

    expect(submitMock).toHaveBeenCalledTimes(1);
    expect(submitMock).toHaveBeenCalledWith(
      expect.stringContaining("We are seeking a Full-Stack AI Engineer"),
      ""
    );
  });

  it("renders progress stepper when status is streaming", () => {
    vi.mocked(useFitReportModule.useFitReport).mockReturnValue({
      ...defaultHookState,
      status: "streaming",
      progress: {
        step: "retrieving_evidence",
        percent: 50,
        message: "Retrieving verified portfolio evidence...",
      },
    });

    render(
      <FitReportModal isOpen={true} onClose={vi.fn()} onAskGap={vi.fn()} />
    );

    expect(screen.getByText("PIPELINE EXECUTION")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText("Retrieving verified portfolio evidence...")).toBeInTheDocument();
  });

  it("renders FitReportCard when status is completed", () => {
    vi.mocked(useFitReportModule.useFitReport).mockReturnValue({
      ...defaultHookState,
      status: "completed",
      report: mockReport,
    });

    render(
      <FitReportModal isOpen={true} onClose={vi.fn()} onAskGap={vi.fn()} />
    );

    expect(screen.getByText("EVALUATION DOSSIER")).toBeInTheDocument();
    expect(screen.getByRole("article", { name: /Job Fit Report: Full-Stack AI Engineer/i })).toBeInTheDocument();
  });

  it("closes modal on close button click and Escape key", () => {
    const handleClose = vi.fn();
    render(
      <FitReportModal isOpen={true} onClose={handleClose} onAskGap={vi.fn()} />
    );

    const closeBtn = screen.getByRole("button", { name: /Close fit report dialog/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(window, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(2);
  });
});
