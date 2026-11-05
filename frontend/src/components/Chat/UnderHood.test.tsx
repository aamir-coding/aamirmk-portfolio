import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { UnderHood } from "./UnderHood";

describe("request receipt", () => {
  it("starts collapsed and provides a native keyboard disclosure", () => {
    render(<UnderHood delivery="instant" />);
    const summary = screen.getByText("Under the hood");
    expect(summary.closest("details")).not.toHaveAttribute("open");
    fireEvent.click(summary);
    expect(summary.closest("details")).toHaveAttribute("open");
    expect(screen.getByText(/None — saved authored response/)).toBeInTheDocument();
  });
  it("never describes cancelled requests as zero-cost", () => {
    render(<UnderHood delivery="cancelled" />);
    expect(screen.getByText(/Unknown \/ incomplete — request stopped/)).toBeInTheDocument();
    expect(screen.queryByText(/None — saved/)).not.toBeInTheDocument();
  });
});
