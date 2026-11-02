import React, { useMemo } from "react";

export interface FormattedMessageProps {
  content: string;
  isStreaming?: boolean;
}

/**
 * Parses inline formatting: **bold**, `code`, [link](url)
 */
function renderInline(text: string): React.ReactNode[] {
  // Regex splitting on:
  // 1) Code: `([^`]+)`
  // 2) Bold: \*\*([^*]+)\*\*
  // 3) Link: \[([^\]]+)\]\((https?:\/\/[^\s)]+)\)
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g;
  const parts = text.split(pattern);

  return parts.map((part, index) => {
    if (!part) return null;

    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      return (
        <code key={index} className="prose-inline-code">
          {part.slice(1, -1)}
        </code>
      );
    }

    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      return (
        <strong key={index} className="prose-strong">
          {part.slice(2, -2)}
        </strong>
      );
    }

    const linkMatch = part.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
    if (linkMatch) {
      const [, label, href] = linkMatch;
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

    return part;
  });
}

interface Block {
  type: "code" | "ul" | "ol" | "quote" | "p";
  content?: string;
  lang?: string;
  items?: string[];
}

/**
 * Splits markdown content into structural blocks:
 * code blocks, unordered lists, ordered lists, blockquotes, and paragraphs.
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

    // 3. Unordered list (- or *)
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

    // 4. Ordered list (1., 2., etc)
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

    // 5. Blockquote (> ...)
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

    // 6. Regular Paragraph
    const paraLines: string[] = [];
    while (i < lines.length) {
      const l = lines[i];
      if (!l) break;
      const t = l.trim();
      if (
        t === "" ||
        t.startsWith("```") ||
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

        if (block.type === "quote" && block.content) {
          return (
            <blockquote key={idx} className="prose-quote">
              <p>
                {renderInline(block.content)}
                {isStreaming && isLastBlock && cursorNode}
              </p>
            </blockquote>
          );
        }

        return (
          <p key={idx} className="prose-paragraph">
            {renderInline(block.content || "")}
            {isStreaming && isLastBlock && cursorNode}
          </p>
        );
      })}
    </div>
  );
});
