import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { FormattedMessage } from "./FormattedMessage";

describe("FormattedMessage", () => {
  it("renders plain text paragraphs", () => {
    const text = "First paragraph.\n\nSecond paragraph.";
    render(<FormattedMessage content={text} />);

    expect(screen.getByText(/First paragraph\./i)).toBeInTheDocument();
    expect(screen.getByText(/Second paragraph\./i)).toBeInTheDocument();
  });

  it("renders inline bold, inline code, and links", () => {
    const text =
      "Built with **FastAPI** and `BM25`. Learn more at [GitHub](https://github.com/aamir).";
    render(<FormattedMessage content={text} />);

    const strong = screen.getByText("FastAPI");
    expect(strong.tagName).toBe("STRONG");

    const code = screen.getByText("BM25");
    expect(code.tagName).toBe("CODE");

    const link = screen.getByRole("link", { name: "GitHub" });
    expect(link).toHaveAttribute("href", "https://github.com/aamir");
  });

  it("renders bullet lists", () => {
    const text = "- Fast response time\n- Sub-second retrieval\n* High test coverage";
    render(<FormattedMessage content={text} />);

    const listItems = screen.getAllByRole("listitem");
    expect(listItems).toHaveLength(3);
    expect(listItems[0]).toHaveTextContent("Fast response time");
    expect(listItems[1]).toHaveTextContent("Sub-second retrieval");
    expect(listItems[2]).toHaveTextContent("High test coverage");
  });

  it("renders numbered lists", () => {
    const text = "1. Parse input\n2. Compute embeddings\n3. Return response";
    render(<FormattedMessage content={text} />);

    const listItems = screen.getAllByRole("listitem");
    expect(listItems).toHaveLength(3);
    expect(listItems[0]).toHaveTextContent("Parse input");
    expect(listItems[1]).toHaveTextContent("Compute embeddings");
    expect(listItems[2]).toHaveTextContent("Return response");
  });

  it("renders fenced code blocks with language header", () => {
    const text = "```python\ndef get_greeting():\n    return 'Hello'\n```";
    render(<FormattedMessage content={text} />);

    expect(screen.getByText("python")).toBeInTheDocument();
    expect(screen.getByText(/def get_greeting/)).toBeInTheDocument();
  });

  it("renders blockquotes", () => {
    const text = "> Engineering is the art of trade-offs.";
    render(<FormattedMessage content={text} />);

    const blockquote = screen.getByRole("blockquote");
    expect(blockquote).toHaveTextContent("Engineering is the art of trade-offs.");
  });

  it("displays streaming cursor when isStreaming is true", () => {
    const text = "Generating response...";
    render(<FormattedMessage content={text} isStreaming={true} />);

    const cursor = screen.getByTestId("streaming-cursor");
    expect(cursor).toBeInTheDocument();
  });
});
