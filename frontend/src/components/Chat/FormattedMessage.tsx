import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

export interface FormattedMessageProps {
  content: string;
  isStreaming?: boolean;
}

function renderWithBreaks(child: React.ReactNode): React.ReactNode {
  if (typeof child !== "string") return child;
  if (!/(<br\s*\/?>|&lt;br\s*\/?&gt;)/i.test(child)) return child;
  const parts = child.split(/(<br\s*\/?>|&lt;br\s*\/?&gt;)/i);
  return parts.map((part, idx) => {
    if (/^(<br\s*\/?>|&lt;br\s*\/?&gt;)$/i.test(part)) {
      return <br key={idx} className="prose-br" />;
    }
    return part;
  });
}

function processChildren(children: React.ReactNode): React.ReactNode {
  if (Array.isArray(children)) {
    return React.Children.map(children, processChildren);
  }
  return renderWithBreaks(children);
}

function sanitizeMarkdown(text: string): string {
  if (!text) return "";
  return text
    // 1. Normalize Unicode non-breaking and zero-width spaces
    .replace(/\u202f/g, " ")
    .replace(/\u00a0/g, " ")
    .replace(/\u200b/g, "")
    // 2. Separate glued list numerals (e.g., "are1. " -> "are\n\n1. ")
    .replace(/([a-zA-Z,:]|[’']s)(\d+\.\s+)/g, "$1\n\n$2")
    // 3. Repair unclosed bold contact headers ONLY when no closing ** exists on the line
    .replace(
      /^([-*]\s+\*\*(?:Email|LinkedIn|Phone(?:\s*\/\s*WhatsApp)?|WhatsApp|GitHub|Website|Contact|Location))\s*(?!.*\*\*):?\s*(.*)$/gim,
      "$1:** $2"
    )
    // 4. Repair protocol omission in bare domain URLs (e.g. "https.linkedin.com" -> "https://linkedin.com")
    .replace(
      /\bhttps?(?::\/\/|\.|\s*)(www\.[^\s<)"'`]+|[a-zA-Z0-9-]+\.(?:com|org|io|dev|app|edu|in|net)(?:\/[^\s<)"'`]*)?)/gi,
      "https://$1"
    );
}

const markdownComponents: Components = {
  p: ({ children }) => (
    <p className="prose-paragraph">{processChildren(children)}</p>
  ),
  h1: ({ children }) => (
    <h1 className="prose-h1">{processChildren(children)}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="prose-h2">{processChildren(children)}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="prose-h3">{processChildren(children)}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="prose-h4">{processChildren(children)}</h4>
  ),
  blockquote: ({ children }) => (
    <blockquote className="prose-quote">{processChildren(children)}</blockquote>
  ),
  hr: () => <hr className="prose-hr" />,
  ul: ({ children }) => <ul className="prose-list prose-ul">{children}</ul>,
  ol: ({ children, start }) => (
    <ol className="prose-list prose-ol" start={start}>
      {children}
    </ol>
  ),
  li: ({ children }) => <li>{processChildren(children)}</li>,
  strong: ({ children }) => (
    <strong className="prose-strong">{children}</strong>
  ),
  em: ({ children }) => <em className="prose-em">{children}</em>,
  del: ({ children }) => <del className="prose-del">{children}</del>,
  a: ({ href, children }) => (
    <a
      className="prose-link"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),
  table: ({ children }) => (
    <div className="prose-table-wrapper">
      <table className="prose-table">{children}</table>
    </div>
  ),
  th: ({ children, ...rest }) => {
    const text = typeof children === "string" ? children.trim() : "";
    const isCompact = /^(#|no\.?|id|rank|step|num|idx)$/i.test(text);
    return (
      <th className={isCompact ? "col-compact" : undefined} {...rest}>
        {processChildren(children)}
      </th>
    );
  },
  td: ({ children, ...rest }) => {
    const text = typeof children === "string" ? children.trim() : "";
    const isCompact = /^\d+$/i.test(text) && text.length <= 4;
    return (
      <td className={isCompact ? "col-compact" : undefined} {...rest}>
        {processChildren(children)}
      </td>
    );
  },
  pre: ({ children }) => {
    const codeElement = React.isValidElement(children) ? children : null;
    const codeProps = (codeElement?.props || {}) as { className?: string };
    const match = /language-(\w+)/.exec(codeProps.className || "");
    const lang = match ? match[1] : undefined;

    return (
      <div className="prose-code-wrapper">
        {lang && (
          <div className="prose-code-header">
            <span className="prose-code-lang">{lang}</span>
          </div>
        )}
        <pre className="prose-code-block">{children}</pre>
      </div>
    );
  },
  code: ({ className, children, ...rest }) => {
    const isInline =
      !className && typeof children === "string" && !children.includes("\n");
    return (
      <code className={isInline ? "prose-inline-code" : className} {...rest}>
        {children}
      </code>
    );
  },
};

export const FormattedMessage = React.memo(function FormattedMessage({
  content,
  isStreaming = false,
}: FormattedMessageProps) {
  const sanitized = useMemo(() => sanitizeMarkdown(content), [content]);

  const cursorNode = (
    <span
      className="streaming-cursor"
      aria-hidden="true"
      data-testid="streaming-cursor"
    >
      ▍
    </span>
  );

  if (!sanitized) {
    return isStreaming ? (
      <div className="chat-message-text">{cursorNode}</div>
    ) : null;
  }

  return (
    <div className="chat-prose">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={markdownComponents}
      >
        {sanitized}
      </ReactMarkdown>
      {isStreaming && cursorNode}
    </div>
  );
});
