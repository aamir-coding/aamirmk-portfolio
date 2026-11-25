import { describe, it, expect, vi } from "vitest";
import { createRef } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { CoverState } from "./CoverState";
import { CandidateDetails, SelectedWork } from "./SelectedWork";

describe("Portfolio introduction and proof", () => {
  it("presents Aamir’s identity as the main heading and a destination for focus", () => {
    const headingRef = createRef<HTMLHeadingElement>();
    render(<CoverState headingRef={headingRef} company={null} />);

    const heading = screen.getByRole("heading", { level: 1, name: /Ask about Aamir/i });
    expect(headingRef.current).toBe(heading);
    expect(heading).toHaveAttribute("tabindex", "-1");
    expect(screen.getByText(/AI Systems & Full-Stack Engineer/i)).toBeInTheDocument();
  });

  it("keeps selected project evidence reachable without sending a message", () => {
    const sample = vi.fn();
    render(<SelectedWork projectId="ai-digital-assistant" onSelect={vi.fn()} onAsk={vi.fn()} onSample={sample} disabled={false} />);
    expect(screen.getByRole("link", { name: "Read the assistant’s evaluation record" })).toHaveAttribute("href", "/evals");
    expect(screen.getByRole("img", { name: /Entropy with its supporting sources/ })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Try the sample answer" }));
    expect(sample).toHaveBeenCalledOnce();
  });

  it("retains credentials, location, and availability", () => {
    render(<CandidateDetails />);

    expect(screen.getByText(/MSRUAS B\.Tech \(CGPA 9\.77\/10\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Bengaluru, India/i)).toBeInTheDocument();
    expect(screen.getByText(/Available for Hire/i)).toBeInTheDocument();
  });
});
