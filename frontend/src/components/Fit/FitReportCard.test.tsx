import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FitReportCard } from "./FitReportCard";
import type { FitReport, SampleJobDescription } from "../../lib/types";

const mockReport: FitReport = {
  role_title: "Senior AI Engineer",
  jd_hash: "a".repeat(64),
  cached: true,
  score: {
    overall_fit: "Strong Match",
    must_have_strong: 3,
    must_have_partial: 1,
    must_have_gap: 0,
    must_have_total: 4,
    nice_to_have_strong: 1,
    nice_to_have_partial: 0,
    nice_to_have_gap: 1,
    nice_to_have_total: 2,
    total_requirements: 6,
    headline: "Direct architectural alignment with Core LLM and FastAPI services.",
  },
  summary:
    "Aamir possesses verified production experience with async FastAPI and Groq API pipelines. He demonstrates strong grounding in hybrid retrieval systems. His minor gap in Kubernetes is addressed by his containerization ramp-up plan.",
  requirements: [
    {
      requirement: {
        id: "req-1",
        text: "3+ years Python and FastAPI experience",
        importance: "must_have",
        type: "skill",
      },
      verdict: "strong",
      evidence_chunk_ids: ["skills-backend", "projects-portfolio"],
      explanation: "Built production FastAPI backend with async streaming SSE.",
    },
    {
      requirement: {
        id: "req-2",
        text: "Kubernetes orchestration in high-scale production",
        importance: "must_have",
        type: "experience",
      },
      verdict: "partial",
      evidence_chunk_ids: ["skills-ramp-up-narratives"],
      explanation: "Docker-native containerization with clear Kubernetes ramp-up plan.",
      ramp_up: "Aamir is actively completing CKA fundamentals and deploying local k8s clusters.",
    },
    {
      requirement: {
        id: "req-3",
        text: "Kafka event streaming at 100k msg/sec",
        importance: "nice_to_have",
        type: "skill",
      },
      verdict: "gap",
      evidence_chunk_ids: [],
      explanation: "No production Kafka experience verified in portfolio facts.",
      downgraded: true,
      ramp_up: "Extrapolates from async Redis and Celery message broker fundamentals.",
    },
  ],
};

const mockPreset: SampleJobDescription = {
  id: "sample-1",
  title: "Senior AI Engineer",
  company: "AI Labs",
  match_expectation: "Strong Match",
  text: "Full job description text with requirements.",
  report: mockReport,
};

describe("<FitReportCard />", () => {
  it("renders role title, overall fit badge, headline, and score metrics", () => {
    render(<FitReportCard report={mockReport} />);

    expect(screen.getByRole("article", { name: /Job Fit Report: Senior AI Engineer/i })).toBeInTheDocument();
    expect(screen.getByText("Strong Match")).toBeInTheDocument();
    expect(screen.getByText("Direct architectural alignment with Core LLM and FastAPI services.")).toBeInTheDocument();
    expect(screen.getByText("3/4")).toBeInTheDocument();
    expect(screen.getByText("Must-Haves Evidenced")).toBeInTheDocument();
  });

  it("renders executive summary synthesis callout", () => {
    render(<FitReportCard report={mockReport} />);

    expect(screen.getByText("EXECUTIVE SYNTHESIS")).toBeInTheDocument();
    expect(screen.getByText(/Aamir possesses verified production experience/i)).toBeInTheDocument();
  });

  it("renders verified citations for supported requirements", () => {
    render(<FitReportCard report={mockReport} />);

    expect(screen.getByText("[skills-backend]")).toBeInTheDocument();
    expect(screen.getByText("[projects-portfolio]")).toBeInTheDocument();
  });

  it("renders anti-overclaiming downgrade banner when downgraded is true", () => {
    render(<FitReportCard report={mockReport} />);

    expect(screen.getByText(/Overclaiming Guard: Model claimed unevidenced match; downgraded to gap/i)).toBeInTheDocument();
  });

  it("renders ramp-up narrative box for gaps and partial alignments", () => {
    render(<FitReportCard report={mockReport} />);

    expect(screen.getByText(/Aamir is actively completing CKA fundamentals/i)).toBeInTheDocument();
    expect(screen.getByText(/Extrapolates from async Redis/i)).toBeInTheDocument();
  });

  it("renders verified golden benchmark banner and JD preview when activePreset is present", () => {
    const handleRerun = vi.fn();
    render(
      <FitReportCard
        report={mockReport}
        activePreset={mockPreset}
        onRerunLive={handleRerun}
      />
    );

    expect(screen.getByText(/CURATED SAMPLE ASSESSMENT \(CACHED SNAPSHOT\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Manually reviewed against current curated facts/i)).toBeInTheDocument();
    expect(screen.getByText(/View Evaluated Job Description/i)).toBeInTheDocument();

    const rerunBtn = screen.getByRole("button", { name: /Re-Run Live Pipeline/i });
    fireEvent.click(rerunBtn);
    expect(handleRerun).toHaveBeenCalledTimes(1);
  });

  it("triggers onAskGap when clicking ask gap action button", () => {
    const handleAskGap = vi.fn();
    render(<FitReportCard report={mockReport} onAskGap={handleAskGap} />);

    const askButtons = screen.getAllByRole("button", { name: /Ask about this in chat/i });
    expect(askButtons.length).toBeGreaterThan(0);
    fireEvent.click(askButtons[0]!);

    expect(handleAskGap).toHaveBeenCalledWith("Kubernetes orchestration in high-scale production");
  });

  it("triggers onReset when clicking analyze custom job description button", () => {
    const handleReset = vi.fn();
    render(<FitReportCard report={mockReport} onReset={handleReset} />);

    const resetBtn = screen.getByRole("button", { name: /Analyze Custom Job Description/i });
    fireEvent.click(resetBtn);

    expect(handleReset).toHaveBeenCalledTimes(1);
  });
});
