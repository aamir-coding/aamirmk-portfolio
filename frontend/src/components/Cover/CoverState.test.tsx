import { describe, it, expect, vi } from "vitest";
import { createRef } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { CoverState } from "./CoverState";
import { CandidateDetails, SelectedWork } from "./SelectedWork";

describe("Portfolio introduction and proof", () => {
  it("presents Aamir’s identity as the main heading and a destination for focus", () => {
    const headingRef = createRef<HTMLHeadingElement>();
    render(<CoverState headingRef={headingRef} company={null} />);

    const heading = screen.getByRole("heading", { level: 1, name: "Aamir Mohammed Khan" });
    expect(headingRef.current).toBe(heading);
    expect(heading).toHaveAttribute("tabindex", "-1");
    expect(screen.getByText(/AI Systems & Full-Stack Engineer/i)).toBeInTheDocument();
  });

  it("keeps selected project evidence reachable without sending a message", () => {
    const onTrySample = vi.fn();
    render(<SelectedWork onTrySample={onTrySample} sampleDisabled={false} />);

    expect(screen.getByRole("heading", { name: "Selected work" })).toHaveAttribute("id", "work");
    expect(screen.getByRole("link", { name: "Open Entropy Online Judge" }))
      .toHaveAttribute("href", "https://entropy-oj.vercel.app/");
    expect(screen.getByRole("link", { name: "Read the assistant’s evaluation record" }))
      .toHaveAttribute("href", "/evals");
    expect(screen.getByRole("link", { name: "View HealthTracker source" }))
      .toHaveAttribute("href", "https://github.com/aamir-coding/health-tracker");
    expect(screen.getAllByRole("img")).toHaveLength(3);
    fireEvent.error(screen.getByRole("img", { name: /Assistant answer about Entropy/ }));
    expect(screen.getByText(/Aamir built Entropy’s coding workspace with compiler diagnostics/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Try the sample answer" }));
    expect(onTrySample).toHaveBeenCalledOnce();
  });

  it("retains credentials, location, and availability", () => {
    render(<CandidateDetails />);

    expect(screen.getByText(/MSRUAS B\.Tech \(CGPA 9\.77\/10\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Bengaluru, India/i)).toBeInTheDocument();
    expect(screen.getByText(/Available for Hire/i)).toBeInTheDocument();
  });
});
