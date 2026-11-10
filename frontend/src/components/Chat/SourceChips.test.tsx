import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SourceChips } from "./SourceChips";
import type { SourceCitation } from "../../lib/types";

describe("SourceChips", () => {
  it("preserves an inaccessible source as a receipt without a broken link", () => {
    render(<SourceChips sources={[{chunk_id:"private-source",title:"Portfolio source",type:"project",source_url:"https://github.com/aamir-coding/aamirmk-portfolio"}]} />);
    expect(screen.getByText("Portfolio source")).toBeInTheDocument();
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.getByTitle(/Source not publicly accessible/)).toBeInTheDocument();
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

    expect(screen.getByText("RECEIPTS:")).toBeInTheDocument();
    expect(screen.getByText("Entropy Online Judge")).toBeInTheDocument();
    expect(screen.getByText("[J1, J2]")).toBeInTheDocument();
    expect(screen.getByText("AlgoUniversity Role")).toBeInTheDocument();
    expect(screen.getByText("[X1]")).toBeInTheDocument();
  });

  it("renders anchor tags with security attributes for sources with URLs", () => {
    const mockSources: SourceCitation[] = [
      {
        chunk_id: "c1",
        title: "Live App Receipt",
        type: "project",
        source_url: "https://entropy-oj.vercel.app",
      },
    ];

    render(<SourceChips sources={mockSources} />);

    const link = screen.getByRole("link", { name: /Live App Receipt/i });
    expect(link).toHaveAttribute("href", "https://entropy-oj.vercel.app");
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
