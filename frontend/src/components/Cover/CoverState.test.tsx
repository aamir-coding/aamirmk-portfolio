import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CoverState } from "./CoverState";

describe("<CoverState />", () => {
  it("renders dossier masthead, identity, core focus, and inquiry prompts", () => {
    const onSelectPrompt = vi.fn();
    render(<CoverState onSelectPrompt={onSelectPrompt} />);

    expect(screen.getByText("CANDIDATE DOSSIER")).toBeInTheDocument();
    expect(screen.getByText("REF: AMK-PORTFOLIO")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /Aamir Mohammed Khan/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/AI Systems & Full-Stack Engineer/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/CORE FOCUS/i)).toBeInTheDocument();
    expect(screen.getByText(/PRIMARY STACK/i)).toBeInTheDocument();
    expect(screen.getByText(/GROUNDING POLICY/i)).toBeInTheDocument();
    expect(screen.getByText(/Suggested Inquiries/i)).toBeInTheDocument();
  });

  it("renders verified candidate credentials ribbon and external touchpoints", () => {
    const onSelectPrompt = vi.fn();
    render(<CoverState onSelectPrompt={onSelectPrompt} />);

    expect(
      screen.getByText(/MSRUAS B\.Tech \(CGPA 9\.77\/10\)/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Bengaluru, India/i)).toBeInTheDocument();
    expect(screen.getByText(/Available for Hire/i)).toBeInTheDocument();

    const githubLink = screen.getByRole("link", { name: /GitHub ↗/i });
    expect(githubLink).toHaveAttribute("href", "https://github.com/aamir-coding");

    const linkedInLink = screen.getByRole("link", { name: /LinkedIn ↗/i });
    expect(linkedInLink).toHaveAttribute("href", "https://www.linkedin.com/in/aamir-mk/");

    const emailLink = screen.getByRole("link", {
      name: /aamirmkh25@gmail\.com ↗/i,
    });
    expect(emailLink).toHaveAttribute("href", "mailto:aamirmkh25@gmail.com");
  });

  it("calls onSelectPrompt when a starter chip is clicked", () => {
    const onSelectPrompt = vi.fn();
    render(<CoverState onSelectPrompt={onSelectPrompt} />);

    const chip = screen.getByRole("button", {
      name: /What is Aamir's experience with FastAPI and LLM systems\?/i,
    });
    fireEvent.click(chip);

    expect(onSelectPrompt).toHaveBeenCalledTimes(1);
    expect(onSelectPrompt).toHaveBeenCalledWith(
      "What is Aamir's experience with FastAPI and LLM systems?"
    );
  });

  it("disables starter chips when disabled prop is true", () => {
    const onSelectPrompt = vi.fn();
    render(<CoverState onSelectPrompt={onSelectPrompt} disabled={true} />);

    const chip = screen.getByRole("button", {
      name: /What is Aamir's experience with FastAPI and LLM systems\?/i,
    });
    expect(chip).toBeDisabled();
  });
});
