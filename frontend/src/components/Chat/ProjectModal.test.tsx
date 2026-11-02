import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProjectModal } from "./ProjectModal";
import type { ProjectCardData } from "../../lib/types";

const mockCard: ProjectCardData = {
  id: "entropy-oj",
  title: "Entropy Online Judge",
  subtitle: "Competitive Programming & DSA Platform with Socratic AI Debugging",
  summary:
    "A competitive-programming platform that compiles and evaluates C++17 submissions.",
  role: "Solo Author",
  tech_stack: ["React 19", "TypeScript", "Redis"],
  highlights: ["Asynchronous worker queue"],
  metrics: { "Worker Model": "Decoupled Redis/BullMQ" },
  github_url: "https://github.com/aamir-coding/entropy-oj",
  live_url: "https://entropy-oj.vercel.app",
  source_sections: ["J1", "J2"],
  architecture_details:
    "### Blueprint Notes\nDecoupled Linux execution runner.",
};

describe("ProjectModal", () => {
  it("renders nothing when isOpen is false", () => {
    const { container } = render(
      <ProjectModal card={mockCard} isOpen={false} onClose={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders accessible modal with title, blueprint, and architecture details when open", () => {
    render(<ProjectModal card={mockCard} isOpen={true} onClose={vi.fn()} />);

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "modal-project-title");

    expect(screen.getByText("Entropy Online Judge")).toBeInTheDocument();
    expect(screen.getByText("BLUEPRINT")).toBeInTheDocument();
    expect(screen.getByText(/Blueprint Notes/i)).toBeInTheDocument();
    expect(screen.getByText(/Decoupled Linux execution runner/i)).toBeInTheDocument();
    expect(screen.getByText("[J1] [J2]")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(<ProjectModal card={mockCard} isOpen={true} onClose={onClose} />);

    const closeBtn = screen.getByRole("button", {
      name: /Close architecture modal/i,
    });
    fireEvent.click(closeBtn);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when dismiss button is clicked", () => {
    const onClose = vi.fn();
    render(<ProjectModal card={mockCard} isOpen={true} onClose={onClose} />);

    const dismissBtn = screen.getByRole("button", {
      name: /Dismiss Dossier/i,
    });
    fireEvent.click(dismissBtn);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when backdrop is clicked", () => {
    const onClose = vi.fn();
    render(<ProjectModal card={mockCard} isOpen={true} onClose={onClose} />);

    const backdrop = screen.getByTestId("modal-backdrop");
    fireEvent.click(backdrop);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Escape key is pressed", () => {
    const onClose = vi.fn();
    render(<ProjectModal card={mockCard} isOpen={true} onClose={onClose} />);

    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("locks body overflow when open and restores on unmount", () => {
    const { unmount } = render(
      <ProjectModal card={mockCard} isOpen={true} onClose={vi.fn()} />
    );

    expect(document.body.style.overflow).toBe("hidden");

    unmount();
    expect(document.body.style.overflow).toBe("");
  });
});
