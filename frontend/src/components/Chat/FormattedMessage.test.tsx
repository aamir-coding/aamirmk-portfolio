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

  it("renders <br> and &lt;br&gt; tags as line breaks without leaking raw tags", () => {
    const text = "First line<br>Second line<br />Third line&lt;br&gt;Fourth line";
    render(<FormattedMessage content={text} />);

    const brs = document.querySelectorAll("br.prose-br");
    expect(brs.length).toBe(3);
    expect(screen.queryByText("<br>")).not.toBeInTheDocument();
    expect(screen.queryByText("<br />")).not.toBeInTheDocument();
    expect(screen.queryByText("&lt;br&gt;")).not.toBeInTheDocument();
  });

  it("renders inline italics (*text* and _text_) and bold italics (***text***)", () => {
    const text =
      "This is *italic one*, _italic two_, and ***bold italic*** with ~~deleted~~ text.";
    render(<FormattedMessage content={text} />);

    const italic1 = screen.getByText("italic one");
    expect(italic1.tagName).toBe("EM");

    const italic2 = screen.getByText("italic two");
    expect(italic2.tagName).toBe("EM");

    const boldItalic = screen.getByText("bold italic");
    expect(boldItalic.closest("em")).toBeInTheDocument();
    expect(boldItalic.closest("strong")).toBeInTheDocument();

    const del = screen.getByText("deleted");
    expect(del.tagName).toBe("DEL");
  });

  it("compacts the '#' index column and assigns col-compact class", () => {
    const text = `
| # | Skill | Projects |
|---|---|---|
| 1 | Full-Stack | Entropy-OJ |
| 2 | Debugging | Redis investigation |
`.trim();

    render(<FormattedMessage content={text} />);

    const table = screen.getByRole("table");
    expect(table).toBeInTheDocument();

    const compactTh = table.querySelector("th.col-compact");
    expect(compactTh).toBeInTheDocument();
    expect(compactTh).toHaveTextContent("#");

    const compactTds = table.querySelectorAll("td.col-compact");
    expect(compactTds).toHaveLength(2);
    expect(compactTds[0]).toHaveTextContent("1");
    expect(compactTds[1]).toHaveTextContent("2");
  });

  it("renders screenshot 2 top 5 skills table and footnote with proper italics and line breaks", () => {
    const text = `
Top 5 Skills - Aamir Mohammed Khan & Where He Applied Them

| # | Skill (as highlighted in his résumé) | Projects/Contexts where the skill was used (see receipts below) |
|---|---|---|
| 1 | AI-Assisted Implementation & Rapid Learning | • Built Entropy-OJ using Claude Code<br>• Developed RAG-powered portfolio assistant |
| 2 | Full-Stack System Integration | • Entropy-OJ: integrated React/TypeScript front-end<br>• Secure Auction System |

*All entries are drawn directly from Aamir's verified résumé and skill inventory.*
`.trim();

    render(<FormattedMessage content={text} />);

    // Table is present with compact col 0
    const compactTh = document.querySelector("th.col-compact");
    expect(compactTh).toBeInTheDocument();
    expect(compactTh).toHaveTextContent("#");

    // Line breaks parsed inside cells
    const cellBrs = document.querySelectorAll("td .prose-br");
    expect(cellBrs.length).toBe(2);

    // Footnote rendered as italic (no raw asterisks leaking)
    const footnote = screen.getByText(
      /All entries are drawn directly from Aamir's verified résumé and skill inventory\./i
    );
    expect(footnote.tagName).toBe("EM");
    expect(
      screen.queryByText(
        /\*All entries are drawn directly from Aamir's verified résumé and skill inventory\.\*/
      )
    ).not.toBeInTheDocument();
  });

  it("normalizes unicode whitespace artifacts and repairs unclosed bold contact lists", () => {
    // String matching the exact problematic pattern with \u202f and unclosed bold tags
    const mangled =
      "Aamir's contact details:\n- **Email\u202faamirmkh25@gmail.com\n- **LinkedIn\u202fhttps.linkedin.com/in/aamir-mk/\n- **Phone / WhatsApp\u202f+91 8904816279";

    render(<FormattedMessage content={mangled} />);

    // Bold tags are repaired
    expect(screen.getByText("Email:")).toBeInTheDocument();
    expect(screen.getByText("Email:").tagName).toBe("STRONG");
    expect(screen.getByText("LinkedIn:")).toBeInTheDocument();
    expect(screen.getByText("LinkedIn:").tagName).toBe("STRONG");
    expect(screen.getByText("Phone / WhatsApp:")).toBeInTheDocument();
    expect(screen.getByText("Phone / WhatsApp:").tagName).toBe("STRONG");

    // Mangled https.linkedin is repaired to clickable link
    const link = screen.getByRole("link", {
      name: "https://linkedin.com/in/aamir-mk/",
    });
    expect(link).toHaveAttribute(
      "href",
      "https://linkedin.com/in/aamir-mk/"
    );
  });

  it("renders URLs wrapped in bold markdown as clickable strong links", () => {
    const text =
      "Profile: **https://www.linkedin.com/in/aamir-mk/**";
    render(<FormattedMessage content={text} />);

    const link = screen.getByRole("link", {
      name: "https://www.linkedin.com/in/aamir-mk/",
    });
    expect(link).toHaveAttribute(
      "href",
      "https://www.linkedin.com/in/aamir-mk/"
    );
    expect(link.closest("strong")).toBeInTheDocument();
  });

  it("renders complex bullet headers (Availability, Work Focus, Location Preference) without mangling", () => {
    const text = `
- **Availability**: Available immediately (from October 2026 onwards)
- **Location Preference**: First choice is onsite or hybrid in **Bengaluru, India**, or remote.
- **Work Focus**: Teams building production-grade software
`.trim();

    render(<FormattedMessage content={text} />);

    expect(screen.getByText("Availability")).toBeInTheDocument();
    expect(screen.getByText("Location Preference")).toBeInTheDocument();
    expect(screen.getByText("Bengaluru, India")).toBeInTheDocument();
    expect(screen.getByText("Work Focus")).toBeInTheDocument();

    // Verify no broken escaped asterisks or misplaced colons leak into text
    expect(screen.queryByText(/Availabilit: y/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Work: Focus/)).not.toBeInTheDocument();
  });

  it("renders loose ordered lists with blank lines as a single continuous sequential list", () => {
    const text = `
1. **AI-Assisted Implementation** – Proficient with Claude Code.

2. **Full-Stack System Integration** – Demonstrated by building Entropy-OJ.

3. **Evidence-Based Debugging** – Uses logs and timestamps.
`.trim();

    render(<FormattedMessage content={text} />);

    const olElements = document.querySelectorAll("ol.prose-ol");
    expect(olElements.length).toBe(1);

    const listItems = screen.getAllByRole("listitem");
    expect(listItems.length).toBe(3);
    expect(listItems[0]).toHaveTextContent(/AI-Assisted Implementation/);
    expect(listItems[1]).toHaveTextContent(/Full-Stack System Integration/);
    expect(listItems[2]).toHaveTextContent(/Evidence-Based Debugging/);
  });

  it("separates glued list numbers into distinct ordered list items", () => {
    const text =
      "Aamir's top three strengths, as highlighted in his résumé, are1. **AI-Assisted Implementation**\n\n2. **Full-Stack System Integration**";

    render(<FormattedMessage content={text} />);

    expect(screen.getByText(/Aamir's top three strengths/)).toBeInTheDocument();
    const listItems = screen.getAllByRole("listitem");
    expect(listItems.length).toBe(2);
    expect(listItems[0]).toHaveTextContent(/AI-Assisted Implementation/);
    expect(listItems[1]).toHaveTextContent(/Full-Stack System Integration/);
  });
});
