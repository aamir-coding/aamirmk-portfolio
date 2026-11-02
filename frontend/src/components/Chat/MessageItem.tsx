import React, { useState, useCallback } from "react";
import type { ChatMessage, ProjectCardData } from "../../lib/types";
import { SourceChips } from "./SourceChips";
import { ProjectCard } from "./ProjectCard";
import { ProjectModal } from "./ProjectModal";
import { FormattedMessage } from "./FormattedMessage";

export interface MessageItemProps {
  message: ChatMessage;
}

export const MessageItem = React.memo(function MessageItem({
  message,
}: MessageItemProps) {
  const isUser = message.role === "user";
  const [activeModalCard, setActiveModalCard] =
    useState<ProjectCardData | null>(null);

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
