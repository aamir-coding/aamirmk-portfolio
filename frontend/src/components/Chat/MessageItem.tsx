import { UnderHood } from "./UnderHood";
import React, { useState, useCallback } from "react";
import type { ChatHistoryMessage, ChatMessage, ProjectCardData } from "../../lib/types";
import { SourceChips } from "./SourceChips";
import { ProjectCard } from "./ProjectCard";
import { ProjectModal } from "./ProjectModal";
import { FormattedMessage } from "./FormattedMessage";
import { DecodeSignal, DecryptedOpening } from "./DecodeSignal";
import { HandoffCard } from "./HandoffCard";
import { AnswerFeedback } from "./AnswerFeedback";

import { projects, type ShowcaseId } from "../Cover/projects";
import { summaryProjectIds } from "../../lib/summary";

export interface MessageItemProps {
  onInspectProject?: (id: ShowcaseId, card?: ProjectCardData) => void;
  message: ChatMessage;
  handoffTranscript?: readonly ChatHistoryMessage[];
}

export const MessageItem = React.memo(function MessageItem({
  message,
  handoffTranscript,
  onInspectProject,
}: MessageItemProps) {
  const isUser = message.role === "user";
  const isStreaming = message.status === "streaming";
  const hasAnswerSources = message.status === "done" && message.delivery !== "cancelled";
  const evidence = !isUser && hasAnswerSources && onInspectProject
    ? summaryProjectIds([...(message.sources ?? []).map(s => s.chunk_id), ...(message.cards ?? []).map(c => c.id)])
    : [];
  const shownProjects = projects.filter(project => evidence.includes(project.id));
  const inlineCards = message.cards?.filter(card => !shownProjects.some(project => project.id === card.id));
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
        <span className="chat-message-author">
          {isUser ? "You" : "AI assistant"}
        </span>
        {message.delivery === "instant" && <span className="chat-message-state">Saved answer</span>}
        {message.delivery === "cancelled" && <span className="chat-message-state">Stopped</span>}
        {message.status === "error" && <span className="chat-message-state">Interrupted</span>}
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
        {message.content ? (
          <div className="answer-typeset">
            <FormattedMessage
              content={message.content}
              isStreaming={isStreaming}
              questionHeading={isUser && message.content.length <= 220 && !message.content.includes("\n")}
            />
            {!isUser && message.status !== "error" && message.delivery !== "cancelled"
              && /[A-Za-z0-9]/.test(message.content) && <DecryptedOpening />}
          </div>
        ) : isStreaming ? (
          <div className="answer-waiting">
            <span className="sr-only" role="status">Preparing an answer…</span>
            <DecodeSignal />
          </div>
        ) : null}
        {message.status === "error" && !message.content && (
          <p className="chat-message-error">
            Generation interrupted or failed.
          </p>
        )}
        {!isUser && hasAnswerSources && message.sources && message.sources.length > 0 && (
          <SourceChips sources={message.sources} />
        )}
        {shownProjects.map(project =>
          <button key={project.id} className="project-evidence" onClick={() => onInspectProject?.(project.id, message.cards?.find(card => card.id === project.id))}>
            View {project.title} evidence
          </button>
        )}
        {!isUser && !isStreaming && inlineCards && inlineCards.length > 0 && (
          <div className="message-cards-tray">
            {inlineCards.map((card) => (
              <ProjectCard
                key={card.id}
                card={card}
                onInspectArchitecture={handleInspectArchitecture}
              />
            ))}
          </div>
        )}
        {!isUser && message.handoffId && handoffTranscript && (
          <HandoffCard id={message.handoffId} transcript={handoffTranscript} />
        )}
        {!isUser && message.status === "done" && message.feedbackId && (
          <AnswerFeedback answerId={message.feedbackId} />
        )}
        {!isUser && !isStreaming ? <UnderHood telemetry={message.telemetry} browserTiming={message.browserTiming} delivery={message.delivery} /> : null}
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
