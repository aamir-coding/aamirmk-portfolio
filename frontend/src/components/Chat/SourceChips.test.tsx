import { fireEvent, render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SourceChips } from "./SourceChips";
import type { SourceCitation } from "../../lib/types";

describe("SourceChips", () => {
  it("preserves an inaccessible source as a receipt without a broken link", () => {
    render(<SourceChips sources={[{chunk_id:"retired-source",title:"Portfolio source",type:"project",source_url:"https://github.com/aamir-coding/portfolio-ai"}]} />);
    expect(screen.getByText("Portfolio source")).toBeInTheDocument();
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.getByText("Reference only")).toBeInTheDocument();
  });
  it("renders nothing when sources array is empty", () => {
    const { container } = render(<SourceChips sources={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders verified receipts container with formatted chips", () => {
    const mockSources: SourceCitation[] = [
      {
        chunk_id: "c1",
        title: "Entropy Online Judge",
        type: "project",
        source_section: "J1, J2",
        source_url: "https://entropy-oj.vercel.app",
      },
      {
        chunk_id: "c2",
        title: "AlgoUniversity Role",
        type: "experience",
        source_section: "X1",
        source_url: null,
      },
    ];

    render(<SourceChips sources={mockSources} />);

    const summary = screen.getByText("Sources");
    expect(summary).toHaveTextContent("Sources 2");
    expect(summary.closest("details")).not.toHaveAttribute("open");
    fireEvent.click(summary);
    expect(summary.closest("details")).toHaveAttribute("open");
    expect(screen.getByText("Entropy Online Judge")).toBeInTheDocument();
    expect(screen.getByText("[J1, J2]")).toBeInTheDocument();
    expect(screen.getByText("AlgoUniversity Role")).toBeInTheDocument();
    expect(screen.getByText("[X1]")).toBeInTheDocument();
  });

  it("renders anchor tags with security attributes for sources with URLs", () => {
    const mockSources: SourceCitation[] = [
      {
        chunk_id: "c1",
        title: "Portfolio source",
        type: "project",
        source_url: "https://github.com/aamir-coding/aamirmk-portfolio",
      },
    ];

    render(<SourceChips sources={mockSources} />);

    fireEvent.click(screen.getByText("Sources"));
    const link = screen.getByRole("link", { name: /Portfolio source/i });
    expect(link).toHaveAttribute("href", "https://github.com/aamir-coding/aamirmk-portfolio");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders non-link span for sources without URLs", () => {
    const mockSources: SourceCitation[] = [
      {
        chunk_id: "c2",
        title: "Direct Résumé Section",
        type: "skill",
        source_section: "S4",
        source_url: null,
      },
    ];

    render(<SourceChips sources={mockSources} />);

    expect(screen.getByText("Direct Résumé Section")).toBeInTheDocument();
    expect(screen.queryByRole("link")).toBeNull();
  });
});
