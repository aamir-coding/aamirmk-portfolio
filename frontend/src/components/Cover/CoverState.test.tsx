import { describe, it, expect } from "vitest";
import { createRef } from "react";
import { render, screen } from "@testing-library/react";
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
    render(<SelectedWork />);

    expect(screen.getByRole("heading", { name: "Selected work" })).toHaveAttribute("id", "work");
    expect(screen.getByRole("link", { name: "Open Entropy Online Judge" }))
      .toHaveAttribute("href", "https://entropy-oj.vercel.app/");
    expect(screen.getByRole("link", { name: "Read the assistant’s evaluation record" }))
      .toHaveAttribute("href", "/evals");
    expect(screen.getByRole("link", { name: "View HealthTracker source" }))
      .toHaveAttribute("href", "https://github.com/aamir-coding/health-tracker");
  });

  it("retains credentials, location, and availability", () => {
    render(<CandidateDetails />);

    expect(screen.getByText(/MSRUAS B\.Tech \(CGPA 9\.77\/10\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Bengaluru, India/i)).toBeInTheDocument();
    expect(screen.getByText(/Available for Hire/i)).toBeInTheDocument();
  });
});
