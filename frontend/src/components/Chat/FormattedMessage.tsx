import React, { useMemo } from "react";

export interface FormattedMessageProps {
  content: string;
  isStreaming?: boolean;
}

/**
 * Parses inline formatting: **bold**, `code`, [label](url), <url>, and bare URLs
 */
function renderInline(text: string): React.ReactNode[] {
  // Regex splitting on:
  // 1) Code: `([^`]+)`
  // 2) Bold: \*\*([^*]+)\*\*
  // 3) Markdown Link: \[([^\]]+)\]\((https?:\/\/[^\s)]+)\)
  // 4) Angle-bracket Link: <(https?:\/\/[^\s>]+)>
  // 5) Bare URL: (https?:\/\/[^\s<)"'`]+)
  const pattern =
    /(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\(https?:\/\/[^\s)]+\)|<https?:\/\/[^\s>]+>|https?:\/\/[^\s<)"'`]+)/g;
  const parts = text.split(pattern);

  return parts.map((part, index) => {
    if (!part) return null;

    // Inline code
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      return (
        <code key={index} className="prose-inline-code">
          {part.slice(1, -1)}
        </code>
      );
    }

    // Bold
    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      return (
        <strong key={index} className="prose-strong">
          {part.slice(2, -2)}
        </strong>
      );
    }

    // Markdown link: [label](url)
    const mdLinkMatch = part.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
    if (mdLinkMatch) {
      const [, label, href] = mdLinkMatch;
      return (
        <a
          key={index}
          href={href}
          className="prose-link"
          target="_blank"
          rel="noopener noreferrer"
        >
          {label}
        </a>
      );
    }

    // Angle-bracket link: <url>
    const angleMatch = part.match(/^<(https?:\/\/[^\s>]+)>$/);
    if (angleMatch) {
      const [, href] = angleMatch;
      return (
        <a
          key={index}
          href={href}
          className="prose-link"
          target="_blank"
          rel="noopener noreferrer"
        >
          {href}
        </a>
      );
    }

    // Bare URL: https://...
    if (/^https?:\/\/[^\s<)"'`]+$/.test(part)) {
      return (
        <a
          key={index}
          href={part}
          className="prose-link"
          target="_blank"
          rel="noopener noreferrer"
        >
          {part}
        </a>
      );
    }

    return part;
  });
}

function splitTableRow(line: string): string[] {
  let trimmed = line.trim();
  if (trimmed.startsWith("|")) trimmed = trimmed.slice(1);
  if (trimmed.endsWith("|")) trimmed = trimmed.slice(0, -1);
  return trimmed.split("|").map((cell) => cell.trim());
}

function isTableSeparator(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed.includes("-") || !trimmed.includes("|")) return false;
  return /^\|?(\s*:?-{2,}:?\s*\|)+\s*:?-{2,}:?\s*\|?$/.test(trimmed);
}

function parseAlignment(cell: string): "left" | "center" | "right" {
  const c = cell.trim();
  const starts = c.startsWith(":");
  const ends = c.endsWith(":");
  if (starts && ends) return "center";
  if (ends) return "right";
  return "left";
}

interface TableBlock {
  type: "table";
  headers: string[];
  alignments?: ("left" | "center" | "right")[];
  rows: string[][];
}

interface HeadingBlock {
  type: "h1" | "h2" | "h3" | "h4";
  content: string;
}

interface HrBlock {
  type: "hr";
}

type Block =
  | { type: "code"; content: string; lang?: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "quote"; content: string }
  | { type: "p"; content: string }
  | HeadingBlock
  | HrBlock
  | TableBlock;

/**
 * Splits markdown content into structural blocks:
 * code blocks, tables, headings, lists, quotes, hr, and paragraphs.
 */
function parseBlocks(markdown: string): Block[] {
  const blocks: Block[] = [];
  const lines = markdown.split(/\r?\n/);
  let i = 0;

  while (i < lines.length) {
    const currentLine = lines[i];
    if (currentLine === undefined) {
      i++;
      continue;
    }

    const trimmed = currentLine.trim();

    // 1. Fenced Code Block
    if (trimmed.startsWith("```")) {
      const lang = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length) {
        const nextLine = lines[i];
        if (nextLine === undefined || nextLine.trim().startsWith("```")) {
          break;
        }
        codeLines.push(nextLine);
        i++;
      }
      if (i < lines.length && lines[i]?.trim().startsWith("```")) {
        i++; // skip closing ```
      }
      blocks.push({
        type: "code",
        lang: lang || undefined,
        content: codeLines.join("\n"),
      });
      continue;
    }

    // 2. Empty line -> skip
    if (trimmed === "") {
      i++;
      continue;
    }

    // 3. Horizontal Rule (---, ***, ___)
    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    // 4. Headings (#, ##, ###, ####)
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch && headingMatch[1] && headingMatch[2]) {
      const level = headingMatch[1].length;
      const type = `h${level}` as "h1" | "h2" | "h3" | "h4";
      blocks.push({
        type,
        content: headingMatch[2].trim(),
      });
      i++;
      continue;
    }

    // 5. Markdown Table (header row with pipes followed by separator row)
    if (
      trimmed.includes("|") &&
      i + 1 < lines.length &&
      isTableSeparator(lines[i + 1] ?? "")
    ) {
      const headerRow = splitTableRow(currentLine);
      const separatorRow = splitTableRow(lines[i + 1] ?? "");
      const alignments = separatorRow.map(parseAlignment);
      i += 2; // advance past header and separator

      const rows: string[][] = [];
      while (i < lines.length) {
        const rowLine = lines[i];
        if (!rowLine || !rowLine.trim().includes("|")) {
          break;
        }
        rows.push(splitTableRow(rowLine));
        i++;
      }

      blocks.push({
        type: "table",
        headers: headerRow,
        alignments,
        rows,
      });
      continue;
    }

    // 6. Unordered list (- or *)
    if (/^[-*]\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length) {
        const l = lines[i];
        if (!l || !/^[-*]\s+/.test(l.trim())) break;
        items.push(l.trim().replace(/^[-*]\s+/, ""));
        i++;
      }
      blocks.push({
        type: "ul",
        items,
      });
      continue;
    }

    // 7. Ordered list (1., 2., etc)
    if (/^\d+\.\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length) {
        const l = lines[i];
        if (!l || !/^\d+\.\s+/.test(l.trim())) break;
        items.push(l.trim().replace(/^\d+\.\s+/, ""));
        i++;
      }
      blocks.push({
        type: "ol",
        items,
      });
      continue;
    }

    // 8. Blockquote (> ...)
    if (trimmed.startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length) {
        const l = lines[i];
        if (!l || !l.trim().startsWith(">")) break;
        quoteLines.push(l.trim().replace(/^>\s?/, ""));
        i++;
      }
      blocks.push({
        type: "quote",
        content: quoteLines.join("\n"),
      });
      continue;
    }

    // 9. Regular Paragraph
    const paraLines: string[] = [];
    while (i < lines.length) {
      const l = lines[i];
      if (!l) break;
      const t = l.trim();
      if (
        t === "" ||
        t.startsWith("```") ||
        /^(\-{3,}|\*{3,}|_{3,})$/.test(t) ||
        /^#{1,4}\s+/.test(t) ||
        (t.includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1] ?? "")) ||
        /^[-*]\s+/.test(t) ||
        /^\d+\.\s+/.test(t) ||
        t.startsWith(">")
      ) {
        break;
      }
      paraLines.push(t);
      i++;
    }
    if (paraLines.length > 0) {
      blocks.push({
        type: "p",
        content: paraLines.join(" "),
      });
    }
  }

  return blocks;
}

export const FormattedMessage = React.memo(function FormattedMessage({
  content,
  isStreaming = false,
}: FormattedMessageProps) {
  const blocks = useMemo(() => parseBlocks(content), [content]);

  const cursorNode = (
    <span
      className="streaming-cursor"
      aria-hidden="true"
      data-testid="streaming-cursor"
    >
      ▍
    </span>
  );

  if (blocks.length === 0) {
    return isStreaming ? (
      <div className="chat-message-text">{cursorNode}</div>
    ) : null;
  }

  return (
    <div className="chat-prose">
      {blocks.map((block, idx) => {
        const isLastBlock = idx === blocks.length - 1;

        if (block.type === "code") {
          return (
            <div key={idx} className="prose-code-wrapper">
              {block.lang && (
                <div className="prose-code-header">
                  <span className="prose-code-lang">{block.lang}</span>
                </div>
              )}
              <pre className="prose-code-block">
                <code>{block.content}</code>
              </pre>
            </div>
          );
        }

        if (block.type === "table") {
          return (
            <div key={idx} className="prose-table-wrapper">
              <table className="prose-table">
                <thead>
                  <tr>
                    {block.headers.map((header, hIdx) => (
                      <th
                        key={hIdx}
                        style={{ textAlign: block.alignments?.[hIdx] ?? "left" }}
                      >
                        {renderInline(header)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {block.rows.map((row, rIdx) => {
                    const isLastRow = rIdx === block.rows.length - 1;
                    return (
                      <tr key={rIdx}>
                        {row.map((cell, cIdx) => {
                          const isLastCell = cIdx === row.length - 1;
                          return (
                            <td
                              key={cIdx}
                              style={{
                                textAlign: block.alignments?.[cIdx] ?? "left",
                              }}
                            >
                              {renderInline(cell)}
                              {isStreaming &&
                                isLastBlock &&
                                isLastRow &&
                                isLastCell &&
                                cursorNode}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          );
        }

        if (block.type === "h1") {
          return (
            <h1 key={idx} className="prose-h1">
              {renderInline(block.content)}
              {isStreaming && isLastBlock && cursorNode}
            </h1>
          );
        }

        if (block.type === "h2") {
          return (
            <h2 key={idx} className="prose-h2">
              {renderInline(block.content)}
              {isStreaming && isLastBlock && cursorNode}
            </h2>
          );
        }

        if (block.type === "h3") {
          return (
            <h3 key={idx} className="prose-h3">
              {renderInline(block.content)}
              {isStreaming && isLastBlock && cursorNode}
            </h3>
          );
        }

        if (block.type === "h4") {
          return (
            <h4 key={idx} className="prose-h4">
              {renderInline(block.content)}
              {isStreaming && isLastBlock && cursorNode}
            </h4>
          );
        }

        if (block.type === "hr") {
          return <hr key={idx} className="prose-hr" />;
        }

        if (block.type === "ul" && block.items) {
          return (
            <ul key={idx} className="prose-list prose-ul">
              {block.items.map((item, itemIdx) => {
                const isLastItem = itemIdx === block.items!.length - 1;
                return (
                  <li key={itemIdx}>
                    {renderInline(item)}
                    {isStreaming && isLastBlock && isLastItem && cursorNode}
                  </li>
                );
              })}
            </ul>
          );
        }

        if (block.type === "ol" && block.items) {
          return (
            <ol key={idx} className="prose-list prose-ol">
              {block.items.map((item, itemIdx) => {
                const isLastItem = itemIdx === block.items!.length - 1;
                return (
                  <li key={itemIdx}>
                    {renderInline(item)}
                    {isStreaming && isLastBlock && isLastItem && cursorNode}
                  </li>
                );
              })}
            </ol>
          );
        }

        if (block.type === "quote") {
          return (
            <blockquote key={idx} className="prose-quote">
              <p>
                {renderInline(block.content)}
                {isStreaming && isLastBlock && cursorNode}
              </p>
            </blockquote>
          );
        }

        if (block.type === "p") {
          return (
            <p key={idx} className="prose-paragraph">
              {renderInline(block.content)}
              {isStreaming && isLastBlock && cursorNode}
            </p>
          );
        }

        return null;
      })}
    </div>
  );
});
