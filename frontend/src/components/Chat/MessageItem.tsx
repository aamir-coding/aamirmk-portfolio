import { UnderHood } from "./UnderHood";
import React, { useState, useCallback } from "react";
import type { ChatHistoryMessage, ChatMessage, ProjectCardData } from "../../lib/types";
import { SourceChips } from "./SourceChips";
import { ProjectCard } from "./ProjectCard";
import { ProjectModal } from "./ProjectModal";
import { FormattedMessage } from "./FormattedMessage";
import { HandoffCard } from "./HandoffCard";
import { AnswerFeedback } from "./AnswerFeedback";

export interface MessageItemProps {
  message: ChatMessage;
  handoffTranscript?: readonly ChatHistoryMessage[];
}

export const MessageItem = React.memo(function MessageItem({
  message,
  handoffTranscript,
}: MessageItemProps) {
  const isUser = message.role === "user";
  const [activeModalCard, setActiveModalCard] =
    useState<ProjectCardData | null>(null);
  const [copied, setCopied] = useState(false);
  const copyTimerRef = React.useRef<number | null>(null);

  React.useEffect(() => {
    return () => {
      if (copyTimerRef.current) {
        window.clearTimeout(copyTimerRef.current);
      }
    };
  }, []);

  const handleCopy = useCallback(async () => {
    if (!message.content) return;
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(message.content);
        setCopied(true);
        if (copyTimerRef.current) {
          window.clearTimeout(copyTimerRef.current);
        }
        copyTimerRef.current = window.setTimeout(() => {
          setCopied(false);
        }, 2000);
      }
    } catch {
      // Graceful fallback if clipboard permission is restricted
    }
  }, [message.content]);

  const handleInspectArchitecture = useCallback((card: ProjectCardData) => {
    setActiveModalCard(card);
  }, []);

  const handleCloseModal = useCallback(() => {
    setActiveModalCard(null);
  }, []);

  return (
    <article
      className={`chat-message ${
        isUser ? "chat-message-user" : "chat-message-assistant"
      }`}
      aria-label={`${isUser ? "User" : "Assistant"} message`}
    >
      <header className="chat-message-header">
        <span className="chat-message-badge">
          {isUser ? "INQUIRY" : "DISPATCH"}
        </span>
        <span className="chat-message-author">
          {isUser ? "Recruiter" : "Aamir.AI"}
        </span>
        <time className="chat-message-time">{message.timestamp}</time>
        {!isUser && message.content && (
          <button
            type="button"
            className={`btn-copy-message ${copied ? "copied" : ""}`.trim()}
            onClick={handleCopy}
            aria-label={copied ? "Copied to clipboard" : "Copy response text"}
            title={copied ? "Copied to clipboard" : "Copy response"}
          >
            {copied ? "Copied ✓" : "Copy"}
          </button>
        )}
      </header>
      <div className="chat-message-body">
        {/* Render generative project cards summoned via tool calls */}
        {!isUser && message.cards && message.cards.length > 0 && (
          <div className="message-cards-tray">
            {message.cards.map((card) => (
              <ProjectCard
                key={card.id}
                card={card}
                onInspectArchitecture={handleInspectArchitecture}
              />
            ))}
          </div>
        )}

        {message.content ? (
          <FormattedMessage
            content={message.content}
            isStreaming={message.status === "streaming"}
          />
        ) : message.status === "streaming" &&
          (!message.cards || message.cards.length === 0) ? (
          <div className="chat-message-text">
            <span
              className="streaming-cursor"
              aria-hidden="true"
              data-testid="streaming-cursor"
            >
              ▍
            </span>
          </div>
        ) : null}
        {message.status === "error" && !message.content && (
          <p className="chat-message-error" role="alert">
            Generation interrupted or failed.
          </p>
        )}
        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceChips sources={message.sources} />
        )}
        {!isUser && message.handoffId && handoffTranscript && (
          <HandoffCard id={message.handoffId} transcript={handoffTranscript} />
        )}
        {!isUser && message.status === "done" && message.feedbackId && (
          <AnswerFeedback answerId={message.feedbackId} />
        )}
        {!isUser && message.status !== "streaming" ? <UnderHood telemetry={message.telemetry} browserTiming={message.browserTiming} delivery={message.delivery} /> : null}
      </div>

      {!isUser && (
        <ProjectModal
          card={activeModalCard}
          isOpen={Boolean(activeModalCard)}
          onClose={handleCloseModal}
        />
      )}
    </article>
  );
});
