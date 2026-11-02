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

  it("renders angle-bracket URLs and bare URLs as clickable links", () => {
    const text =
      "Live at <https://entropy-oj.vercel.app> or check https://aamirmk-portfolio.vercel.app for details.";
    render(<FormattedMessage content={text} />);

    const angleLink = screen.getByRole("link", {
      name: "https://entropy-oj.vercel.app",
    });
    expect(angleLink).toHaveAttribute("href", "https://entropy-oj.vercel.app");

    const bareLink = screen.getByRole("link", {
      name: "https://aamirmk-portfolio.vercel.app",
    });
    expect(bareLink).toHaveAttribute(
      "href",
      "https://aamirmk-portfolio.vercel.app"
    );
  });

  it("renders markdown tables with headers, cells, and inline links", () => {
    const text = `
| Project | Core purpose | Live Link |
| :--- | :---: | ---: |
| **Entropy-OJ** | Online Judge | <https://entropy-oj.vercel.app> |
| **Portfolio** | AI Assistant | <https://aamirmk-portfolio.vercel.app> |
`.trim();

    render(<FormattedMessage content={text} />);

    const table = screen.getByRole("table");
    expect(table).toBeInTheDocument();

    const columnHeaders = screen.getAllByRole("columnheader");
    expect(columnHeaders).toHaveLength(3);
    expect(columnHeaders[0]).toHaveTextContent("Project");
    expect(columnHeaders[1]).toHaveTextContent("Core purpose");
    expect(columnHeaders[2]).toHaveTextContent("Live Link");

    const cells = screen.getAllByRole("cell");
    expect(cells).toHaveLength(6);
    expect(cells[0]).toHaveTextContent("Entropy-OJ");
    expect(cells[2]?.querySelector("a")).toHaveAttribute(
      "href",
      "https://entropy-oj.vercel.app"
    );
  });

  it("renders the user's project table and overall production impact smoothly", () => {
    const text = `
Aamir Mohammed Khan's most notable production-grade projects are:

| Project | Core purpose | Architecture highlights (from his résumé) | Production impact |
|---------|--------------|--------------------------------------------|-------------------|
| **Entropy-OJ** | Competitive programming | React + TS; Node API; Docker | Live at <https://entropy-oj.vercel.app>. |
| **AI Digital Assistant** | RAG assistant | FastEmbed ONNX + BM25 | Deployed at <https://aamirmk-portfolio.vercel.app>. |

**Overall production impact** - All listed applications are publicly deployed.
`.trim();

    render(<FormattedMessage content={text} />);

    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(
      screen.getByText("Architecture highlights (from his résumé)")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "https://entropy-oj.vercel.app" })
    ).toBeInTheDocument();
    expect(
      screen.getByText("Overall production impact")
    ).toBeInTheDocument();
  });

  it("renders headings and horizontal rules", () => {
    const text = "# Heading 1\n## Heading 2\n---\n### Heading 3";
    render(<FormattedMessage content={text} />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Heading 1"
    );
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent(
      "Heading 2"
    );
    expect(screen.getByRole("heading", { level: 3 })).toHaveTextContent(
      "Heading 3"
    );
    expect(document.querySelector("hr")).toBeInTheDocument();
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
