import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProjectCard } from "./ProjectCard";
import type { ProjectCardData } from "../../lib/types";

const mockCard: ProjectCardData = {
  id: "entropy-oj",
  title: "Entropy Online Judge",
  subtitle: "Competitive Programming & DSA Platform with Socratic AI Debugging",
  summary:
    "A competitive-programming platform that compiles and evaluates C++17 and Python 3.11 submissions.",
  role: "Solo Author",
  tech_stack: ["React 19", "TypeScript", "BullMQ", "Redis", "GCC"],
  highlights: [
    "Asynchronous execution queue decoupling judging from HTTP",
    "Socratic Hint Engine protecting hidden test cases",
  ],
  metrics: {
    "Worker Model": "Decoupled Redis/BullMQ",
    "Sandboxing": "Linux OS Limits",
  },
  github_url: "https://github.com/aamir-coding/entropy-oj",
  live_url: "https://entropy-oj.vercel.app",
  source_sections: ["J1", "J2", "J4"],
  architecture_details: "Detailed system architecture notes",
};

describe("ProjectCard", () => {
  it("renders project card header, role badge, title and subtitle", () => {
    render(<ProjectCard card={mockCard} />);

    expect(screen.getByText("Entropy Online Judge")).toBeInTheDocument();
    expect(screen.getByText("Solo Author")).toBeInTheDocument();
    expect(screen.getByText("VERIFIED RECEIPT")).toBeInTheDocument();
    expect(
      screen.getByText(/Competitive Programming & DSA Platform/i)
    ).toBeInTheDocument();
  });

  it("renders tech stack chips and highlights", () => {
    render(<ProjectCard card={mockCard} />);

    expect(screen.getByText("React 19")).toBeInTheDocument();
    expect(screen.getByText("BullMQ")).toBeInTheDocument();
    expect(
      screen.getByText(/Asynchronous execution queue decoupling/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Worker Model:")).toBeInTheDocument();
    expect(screen.getByText("Decoupled Redis/BullMQ")).toBeInTheDocument();
  });

  it("renders external links with target blank and rel attributes", () => {
    render(<ProjectCard card={mockCard} />);

    const liveLink = screen.getByRole("link", { name: /Live Demo/i });
    expect(liveLink).toHaveAttribute("href", "https://entropy-oj.vercel.app");
    expect(liveLink).toHaveAttribute("target", "_blank");

    const repoLink = screen.getByRole("link", { name: /Repository/i });
    expect(repoLink).toHaveAttribute(
      "href",
      "https://github.com/aamir-coding/entropy-oj"
    );
  });

  it("triggers onInspectArchitecture callback on action click", () => {
    const onInspect = vi.fn();
    render(<ProjectCard card={mockCard} onInspectArchitecture={onInspect} />);

    const inspectBtn = screen.getByRole("button", {
      name: /Inspect Architecture/i,
    });
    fireEvent.click(inspectBtn);

    expect(onInspect).toHaveBeenCalledTimes(1);
    expect(onInspect).toHaveBeenCalledWith(mockCard);
  });
});
